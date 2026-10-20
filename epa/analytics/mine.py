"""Run PM4Py discovery and conformance and save every numerical result."""
import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path
import pandas as pd
import pm4py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from pm4py.objects.log.obj import EventLog,Trace,Event
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from .reference_nets import build
from services.domain import TASKS

pm4py.util.constants.SHOW_PROGRESS_BAR=False

def frame_to_log(frame):
    log=EventLog()
    for case_id,group in frame.groupby('case_id',sort=True):
        trace=Trace(attributes={'concept:name':str(case_id)})
        for row in group.sort_values(['timestamp','event_index']).to_dict('records'):
            trace.append(Event({'concept:name':row['task_id'],'time:timestamp':row['timestamp'].to_pydatetime(),
                'start_timestamp':row['start_timestamp'].to_pydatetime(),'org:resource':row['resource'],
                'lifecycle:transition':'complete','activity_label':row['activity']}))
        log.append(trace)
    return log

def save_net(net,im,fm,path):
    pm4py.write_pnml(net,im,fm,str(path.with_suffix('.pnml')))
    graph=pn_visualizer.apply(net,im,fm,parameters={'format':'svg'})
    path.with_suffix('.dot').write_text(graph.source)
    # Portable fallback: draw the actual mined net without a Graphviz binary.
    g=nx.DiGraph()
    for p in net.places:g.add_node('p:'+str(p.name),kind='place',obj=p)
    for t in net.transitions:g.add_node('t:'+str(t.name),kind='transition',obj=t)
    def key(obj):return ('p:' if obj in net.places else 't:')+str(obj.name)
    for a in net.arcs:g.add_edge(key(a.source),key(a.target))
    # Condensation assigns layers even when the mined net contains loops.
    scc=nx.condensation(g);level={}
    for c in nx.topological_sort(scc):level[c]=max([level[p]+1 for p in scc.predecessors(c)] or [0])
    groups={}
    for name in sorted(g):groups.setdefault(level[scc.graph['mapping'][name]],[]).append(name)
    pos={name:(x,(j-(len(names)-1)/2)*1.5) for x,names in groups.items() for j,name in enumerate(names)}
    fig,ax=plt.subplots(figsize=(min(22,max(10,len(groups)*1.0)),max(4,max(map(len,groups.values()))*1.0)))
    pnodes=[n for n in g if g.nodes[n]['kind']=='place'];tnodes=[n for n in g if n not in pnodes]
    nx.draw_networkx_edges(g,pos,ax=ax,arrows=True,arrowsize=11,node_size=260,width=.85,connectionstyle='arc3,rad=0.04')
    nx.draw_networkx_nodes(g,pos,nodelist=pnodes,node_size=160,node_color='white',edgecolors='#344b5c',ax=ax)
    nx.draw_networkx_nodes(g,pos,nodelist=tnodes,node_shape='s',node_size=380,node_color='#e7eff7',edgecolors='#344b5c',ax=ax)
    labels={n:(g.nodes[n]['obj'].label or 'τ') for n in tnodes}
    nx.draw_networkx_labels(g,pos,labels,font_size=9,ax=ax)
    for place,count in im.items():
        x,y=pos[key(place)];ax.text(x,y,'●',ha='center',va='center',fontsize=5)
    for place,count in fm.items():
        x,y=pos[key(place)];ax.scatter([x],[y],s=100,facecolors='none',edgecolors='#344b5c')
    ax.set_title(path.name.replace('_',' ')+'  |  rectangles = activities, circles = places',fontsize=12)
    ax.axis('off');fig.tight_layout();fig.savefig(path.with_suffix('.png'),dpi=180);fig.savefig(path.with_suffix('.svg'));plt.close(fig)

def mine(input_path=Path('results/event_log.csv'),output=Path('results')):
    output.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(input_path)
    for col in ['timestamp','start_timestamp']:df[col]=pd.to_datetime(df[col],utc=True,format='ISO8601')
    df=df.sort_values(['case_id','timestamp','event_index'])
    summary={'tool':'PM4Py','pm4py_version':pm4py.__version__,'data_kind':'simulated',
             'discovery_split':'First 80% of sorted case IDs train; remaining 20% test within each process',
             'processes':{}}
    variants=[];bottlenecks=[];nets=output/'mined_models';nets.mkdir(exist_ok=True)
    for process,sub in df.groupby('process'):
        log=frame_to_log(sub);pm4py.write_xes(log,str(output/(process+'.xes')))
        ids=sorted(sub.case_id.unique());cut=max(1,int(len(ids)*.8));train=frame_to_log(sub[sub.case_id.isin(ids[:cut])])
        test=frame_to_log(sub[sub.case_id.isin(ids[cut:])]);test=test if test else train
        sequences=[tuple(e['concept:name'] for e in trace) for trace in log]
        frequencies=Counter(sequences)
        for variant,count in frequencies.most_common():variants.append({'process':process,'variant':' > '.join(variant),'cases':count})
        dfg=Counter((a,b) for seq in sequences for a,b in zip(seq,seq[1:]));acts=sorted({a for seq in sequences for a in seq})
        footprint={a:{b:('||' if (a,b) in dfg and (b,a) in dfg else '->' if (a,b) in dfg else '<-' if (b,a) in dfg else '#') for b in acts} for a in acts}
        with (output/(process+'_footprint.csv')).open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['activity']+acts)
            for a in acts:w.writerow([a]+[footprint[a][b] for b in acts])
        discovery={}
        for name,method in [('alpha',pm4py.discover_petri_net_alpha),('inductive',pm4py.discover_petri_net_inductive)]:
            net,im,fm=method(train);save_net(net,im,fm,nets/(process+'_'+name))
            fitness=pm4py.fitness_token_based_replay(test,net,im,fm)
            discovery[name]={'places':len(net.places),'transitions':len(net.transitions),
                             'held_out_token_fitness':fitness,
                             'place_labels':[str(p.name) for p in sorted(net.places,key=lambda p:str(p.name))]}
        reference,im,fm=build(process);pm4py.write_pnml(reference,im,fm,str(nets/(process+'_reference.pnml')))
        reference_fitness=pm4py.fitness_token_based_replay(log,reference,im,fm)
        # Deliberately remove a prerequisite, independent of discovery training.
        removed={'P1':'A7','P2':'V4','P3':'I7'}[process]
        candidate=next(trace for trace in log if any(e['concept:name']==removed for e in trace))
        bad=EventLog([Trace([Event(dict(e)) for e in candidate if e['concept:name']!=removed],attributes={'concept:name':'negative'})])
        negative=pm4py.fitness_token_based_replay(bad,reference,im,fm)
        grouped=sub.groupby('case_id')
        cycles=(grouped.timestamp.max()-grouped.start_timestamp.min()).dt.total_seconds()/3600
        rework={cid:int((g.task_id=='A3').sum()) for cid,g in grouped}
        outcome_counts=grouped.outcome.first().value_counts().to_dict()
        stats={'cases':len(ids),'events':len(sub),'variants':len(frequencies),
               'cycle_hours_mean':float(cycles.mean()),'cycle_hours_median':float(cycles.median()),
               'cycle_hours_p90':float(cycles.quantile(.9)),'outcomes':{str(k):int(v) for k,v in outcome_counts.items()},
               'train_cases':len(train),'test_cases':len(test),'discovery':discovery,
               'reference_control_flow_fitness':reference_fitness,
               'negative_control':{'removed_task':removed,'fitness':negative},
               'alpha_sets':{'T':acts,'TI':sorted({s[0] for s in sequences}),'TO':sorted({s[-1] for s in sequences}),
                             'directly_follows':{a+'>'+b:n for (a,b),n in sorted(dfg.items())},
                             'concurrency_pairs':[[a,b] for a in acts for b in acts if a<b and footprint[a][b]=='||']}}
        if process=='P1':
            requested=[cid for cid,count in rework.items() if count]
            no_request=[cid for cid,count in rework.items() if not count]
            stats['information_request_cases']=len(requested)
            stats['mean_cycle_with_information_request']=float(cycles.loc[requested].mean())
            stats['mean_cycle_without_information_request']=float(cycles.loc[no_request].mean())
            stats['repeat_information_round_cases']=sum(count>1 for count in rework.values())
        task_stats=sub.groupby('task_id').agg(executions=('case_id','count'),mean_active_hours=('active_hours','mean'),mean_wait_hours=('wait_hours','mean'))
        for task,row in task_stats.iterrows():
            bottlenecks.append({'process':process,'task_id':task,'activity':TASKS[task][0],**{k:float(v) for k,v in row.items()}})
        summary['processes'][process]=stats
    pd.DataFrame(variants).to_csv(output/'variants.csv',index=False)
    pd.DataFrame(bottlenecks).to_csv(output/'task_performance.csv',index=False)
    (output/'analytics_summary.json').write_text(json.dumps(summary,indent=2,default=float))
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].bar(list(summary['processes']),[s['cycle_hours_mean'] for s in summary['processes'].values()],color=['#315979','#5c7a63','#9c7434'])
    axes[0].set_ylabel('Mean simulated case duration in hours');axes[0].set_title('Case duration by process')
    b=pd.DataFrame(bottlenecks);b=b[b.task_id!='A5'].nlargest(6,'mean_wait_hours').sort_values('mean_wait_hours')
    axes[1].barh(b.task_id,b.mean_wait_hours,color='#315979');axes[1].set_xlabel('Mean simulated queue time in hours')
    axes[1].set_title('Largest queue delays excluding the timer')
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(output/'performance.png',dpi=220);fig.savefig(output/'performance.svg');plt.close(fig)
    print(json.dumps({p:{'cases':s['cases'],'events':s['events'],'mean_hours':round(s['cycle_hours_mean'],2),
        'reference_fitness':s['reference_control_flow_fitness']['log_fitness']} for p,s in summary['processes'].items()},indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=Path('results/event_log.csv'))
    p.add_argument('--output',type=Path,default=Path('results'));a=p.parse_args();mine(a.input,a.output)
