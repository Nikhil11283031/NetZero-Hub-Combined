"""Read and export endpoints used by the React module; no extra business service."""
import csv
import io
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Literal
from fastapi import Depends, Response
from .common import principal, authorise


def register_read_api(app, store, *, licences=False):
    @app.get('/me')
    def me(user=Depends(principal)):
        authorise(user)
        return user

    @app.get('/cases')
    def cases(user=Depends(principal)):
        return store.list_owned('cases', user)

    @app.get('/cases/{case_id}/events')
    def case_events(case_id: str, user=Depends(principal)):
        authorise(user, store.get(case_id))
        return store.events(case_id)

    if licences:
        @app.get('/licences')
        def list_licences(user=Depends(principal)):
            return store.list_owned('licences', user)

    @app.get('/events/export')
    def export(format: Literal['csv', 'xes'] = 'csv', user=Depends(principal)):
        authorise(user, officer=True)
        events = store.events()
        if format == 'csv':
            stream = io.StringIO(newline='')
            columns = ['case_id', 'process', 'task_id', 'activity', 'timestamp', 'resource', 'actor', 'seq']
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(events)
            body, media = stream.getvalue(), 'text/csv'
        else:
            log = ET.Element('log', {'xes.version': '1.0', 'xes.features': 'nested-attributes',
                                    'xmlns': 'http://www.xes-standard.org/'})
            for name, prefix in [('Concept', 'concept'), ('Time', 'time'), ('Organizational', 'org'), ('Lifecycle', 'lifecycle')]:
                ET.SubElement(log, 'extension', {'name': name, 'prefix': prefix,
                    'uri': f'http://www.xes-standard.org/{name.lower()}.xesext'})
            ET.SubElement(log, 'classifier', {'name': 'Activity', 'keys': 'concept:name'})
            traces = defaultdict(list)
            for event in events:
                traces[event['case_id']].append(event)
            for case_id, trace_events in traces.items():
                trace = ET.SubElement(log, 'trace')
                ET.SubElement(trace, 'string', {'key': 'concept:name', 'value': case_id})
                ET.SubElement(trace, 'string', {'key': 'process', 'value': trace_events[0]['process']})
                for entry in trace_events:
                    event = ET.SubElement(trace, 'event')
                    for key, value in [('concept:name', entry['activity']), ('task_id', entry['task_id']),
                                       ('org:resource', entry['resource']), ('lifecycle:transition', 'complete')]:
                        ET.SubElement(event, 'string', {'key': key, 'value': value})
                    ET.SubElement(event, 'date', {'key': 'time:timestamp', 'value': entry['timestamp']})
            body, media = ET.tostring(log, encoding='utf-8', xml_declaration=True), 'application/xml'
        return Response(body, media_type=media,
                        headers={'Content-Disposition': f'attachment; filename="epa-events.{format}"'})
