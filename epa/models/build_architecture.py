"""SoaML/UML SVG sources and schema-based ArchiMate exchange model."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from .build_models import Canvas,OUT,ROOT

def soaml():
    c=Canvas(1540,890)
    c.text(35,38,'C1 Services architecture and participant ports',size=29,width=110)
    c.ellipse(35,80,1470,680,dashed=True)
    c.text(770,120,'«ServicesArchitecture» NetZero environmental services',size=24,center=True,width=95)
    c.rect(100,345,300,155,'«Participant»\nconsumer : NetZeroHub',size=25)
    c.rect(1120,345,310,155,'«Participant»\nprovider : NSW EPA',size=25)
    c.ellipse(545,180,450,160,'«ServiceContract»\nLicenceManagementContract\nEPA-001',dashed=True)
    c.ellipse(545,540,450,160,'«ServiceContract»\nPollutionManagementContract\nEPA-002',dashed=True)
    for y in [365,455]:
        c.rect(390,y,20,20,fill='white');c.rect(1110,y,20,20,fill='white')
    c.line([(410,375),(490,375),(545,260)],dashed=True,arrow=False)
    c.line([(995,260),(1040,375),(1110,375)],dashed=True,arrow=False)
    c.line([(410,465),(490,465),(545,620)],dashed=True,arrow=False)
    c.line([(995,620),(1040,465),(1110,465)],dashed=True,arrow=False)
    c.text(170,315,'«Request» ports',size=22,width=30);c.text(1150,315,'«Service» ports',size=22,width=30)
    c.text(460,395,'licence consumer',size=19,width=14);c.text(1020,300,'licence provider',size=19,width=14)
    c.text(470,520,'reporter',size=19,width=14);c.text(1010,575,'investigator',size=19,width=14)
    c.text(40,808,'Dashed ellipse = UML collaboration. Dashed connectors bind participant roles to service contract roles.',size=22,width=125)
    c.text(40,845,'The platform aggregates the services; licensing and regulatory decisions remain with the provider role.',size=22,width=125)
    c.save('C1_SoaML_architecture')

    c=Canvas(1580,1040)
    c.text(35,38,'C2 Service interfaces and message types',size=29,width=110)
    boxes=[(45,100,710,405,'«ServiceInterface» LicenceManagement',[
      '+ submitApplication(Application) : CaseReceipt', '+ getCase(caseId) : CaseStatus',
      '+ provideInformation(InformationCommand) : CaseStatus',
      '+ submitVariation(VariationRequest) : CaseReceipt',
      '+ getLicence(licenceId) : LicenceRecord',
      'Provided interface: ILicensingRequests', 'Required interface: none for request and reply']),
      (825,100,710,405,'«ServiceInterface» PollutionManagement',[
      '+ submitReport(IncidentReport) : CaseReceipt', '+ getCase(caseId) : CaseStatus',
      '+ triage(caseId, version, RiskDecision) : CaseStatus',
      '+ recordEvidence(caseId, version, Evidence) : CaseStatus',
      '+ conclude(caseId, version, Finding) : CaseStatus',
      'Provided interface: IIncidentRequests', 'Required interface: ILicenceContext']),
      (45,590,710,350,'«ServiceInterface» LicenceContext',[
      '+ getContext(licenceId) : LicenceContextRecord',
      'Provider: LicenceService participant', 'Consumer: IncidentService participant',
      'Record: id, active, version, conditions', 'No applicant or reporter personal details']),
      (825,590,710,350,'«MessageType» Shared data contracts',[
      'CaseReceipt: caseId, processId, state, version',
      'Command: expectedVersion, action, values',
      'Decision: approved or substantiated, rationale',
      'CaseStatus: owner-authorised case fields',
      'All IDs opaque strings; timestamps ISO 8601 with zone'])]
    for x,y,w,h,title,lines in boxes:
        c.rect(x,y,w,h,fill='white');c.text(x+w/2,y+38,title,size=24,center=True,width=60)
        c.line([(x,y+62),(x+w,y+62)],arrow=False)
        for n,line in enumerate(lines):c.text(x+18,y+99+n*40,line,size=21,width=58)
    c.text(40,1008,'Read-only polling returns outcomes. A callback interface is not assumed or implemented.',size=22,width=130)
    c.save('C2_SoaML_interfaces')

    def protocol(name,title,lanes,messages,frames):
        c=Canvas(1600,1080);c.text(35,38,title,size=29,width=110)
        xs=[190,590,990,1390]
        for x,lane in zip(xs,lanes):
            c.rect(x-135,80,270,85,lane,size=21);c.line([(x,165),(x,1010)],dashed=True,arrow=False)
        for y,start,end,label,dashed in messages:
            c.line([(xs[start],y),(xs[end],y)],dashed=dashed)
            c.text((xs[start]+xs[end])/2,y-12,label,size=21,center=True,width=66)
        for x,y,w,h,label in frames:
            c.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#708392" stroke-width="2"/>')
            c.text(x+10,y+23,label,size=19,width=85)
        c.save(name)
    protocol('C3_Licence_contract','C3 Licence application contract behaviour',
      ['applicant : Consumer','hub : NetZeroHub','licensing : Provider','officer : DecisionRole'],[
      (225,0,1,'Application request',False),(285,1,2,'submitApplication(Application)',False),
      (340,2,1,'CaseReceipt and version',True),(380,3,2,'Check completeness',False),
      (455,1,2,'getCase → information request',False),(510,1,2,'provideInformation and expectedVersion',False),
      (565,3,2,'Recheck completeness',False),
      (680,3,2,'Record both required assessments',False),(750,3,2,'approve or refuse with rationale',False),
      (870,1,2,'getCase(caseId)',False),(930,2,1,'Authorised outcome and licence if approved',True),
      (985,1,0,'Show outcome',True)],[(445,405,1090,205,'loop [information needed and timer not expired]'),
                              (445,635,1090,155,'opt [complete application]')])
    protocol('C4_Incident_contract','C4 Incident contract and licence context composition',
      ['reporter : Consumer','hub : NetZeroHub','incident : Provider','licensing : ContextProvider'],[
      (225,0,1,'Pollution report',False),(290,1,2,'submitReport(IncidentReport)',False),
      (350,2,1,'CaseReceipt plus immediate safety guidance',True),
      (420,1,2,'Officer records triage',False),
      (520,2,1,'Emergency or referral guidance',True),
      (635,2,3,'getContext(licenceId) with service token',False),
      (695,3,2,'Context or no match; timeout → retry later',True),
      (780,1,2,'Officer records evidence and conclusion',False),
      (870,1,2,'getCase(caseId)',False),(935,2,1,'Permitted outcome or referral guidance',True),
      (990,1,0,'Show outcome',True)],[(480,460,1050,105,'opt [emergency or other authority]'),
                                  (480,580,1050,240,'opt [non emergency and EPA jurisdiction]')])

    c=Canvas(1580,860);c.text(35,38,'C5 Participant architecture and composition',size=29,width=110)
    c.rect(40,310,300,150,'«Participant»\nNetZeroHub\nrequest ports',size=25)
    c.rect(420,90,1110,690,fill='white');c.text(970,130,'«ParticipantArchitecture» NSW EPA service slice',size=25,center=True,width=70)
    c.rect(570,225,360,170,'«Participant»\nLicenceService\nprovides LicenceManagement\nand LicenceContext',size=23)
    c.rect(570,515,360,170,'«Participant»\nIncidentService\nprovides PollutionManagement\nrequires LicenceContext',size=23)
    c.rect(1120,230,340,160,'Owned licence data\nApplications and variations\nLicence versions',size=23)
    c.rect(1120,520,340,160,'Owned incident data\nReports and evidence\nInvestigation outcomes',size=23)
    c.line([(340,345),(450,345),(450,310),(570,310)],label='EPA-001')
    c.line([(340,425),(450,425),(450,600),(570,600)],label='EPA-002')
    c.line([(930,600),(1030,600),(1030,420),(750,420),(750,395)],label='LicenceContext')
    c.line([(930,310),(1120,310)],label='owns')
    c.line([(930,650),(1060,650),(1060,665),(1120,665)],label='owns')
    c.text(45,820,'Two business services and two deployed microservices. Licence context is an internal interface of EPA-001.',size=22,width=130)
    c.save('C5_SoaML_composition')

def archimate():
    # Each tuple records ID, ArchiMate type, label, x, y, width, height.
    es=[('epa','BusinessActor','NSW EPA',70,110,250,90),
      ('roleL','BusinessRole','Licensing officer',410,110,280,90),('roleI','BusinessRole','Investigator',1230,110,280,90),
      ('bpL','BusinessProcess','Licence lifecycle P1 and P2',410,285,280,115),
      ('bpI','BusinessProcess','Pollution investigation P3',1230,285,280,115),
      ('bsL','BusinessService','EPA-001 Licence management',790,200,300,115),
      ('bsI','BusinessService','EPA-002 Pollution management',1620,200,300,115),
      ('asL','ApplicationService','Licence workflow API',410,535,280,100),
      ('asI','ApplicationService','Incident workflow API',1230,535,280,100),
      ('afL','ApplicationFunction','Validate assess decide and version',410,730,280,120),
      ('afI','ApplicationFunction','Triage collect review and conclude',1230,730,280,120),
      ('acL','ApplicationComponent','LicenceService',410,930,280,100),
      ('acI','ApplicationComponent','IncidentService',1230,930,280,100),
      ('acUI','ApplicationComponent','React EPA feature module',810,930,360,100),
      ('doL','DataObject','Licence case and conditions',60,725,260,120),
      ('doI','DataObject','Incident case and evidence',1640,725,260,120),
      ('tsL','TechnologyService','HTTP execution and persistence',410,1130,280,115),
      ('tsI','TechnologyService','HTTP execution and persistence',1230,1130,280,115),
      ('tsUI','TechnologyService','Web delivery and API proxy',810,1130,360,115),
      ('host','Node','Local browser Node Python and SQLite',810,1315,360,110),
      ('artL','Artifact','licensing.sqlite',60,1135,260,110),
      ('artI','Artifact','incidents.sqlite',1640,1135,260,110)]
    rs=[('Assignment','epa','roleL'),('Assignment','epa','roleI'),('Assignment','roleL','bpL'),('Assignment','roleI','bpI'),
        ('Realization','bpL','bsL'),('Realization','bpI','bsI'),('Serving','asL','bpL'),('Serving','asI','bpI'),
        ('Realization','afL','asL'),('Realization','afI','asI'),('Assignment','acL','afL'),('Assignment','acI','afI'),
        ('Access','afL','doL'),('Access','afI','doI'),('Serving','tsL','acL'),('Serving','tsI','acI'),
        ('Realization','host','tsL'),('Realization','host','tsI'),('Realization','artL','doL'),('Realization','artI','doI'),
        ('Serving','asL','acUI'),('Serving','asI','acUI'),('Serving','tsUI','acUI'),('Realization','host','tsUI')]
    ns='http://www.opengroup.org/xsd/archimate/3.0/';xsi='http://www.w3.org/2001/XMLSchema-instance'
    ET.register_namespace('',ns);ET.register_namespace('xsi',xsi)
    def sub(parent,name,**attrs):return ET.SubElement(parent,'{'+ns+'}'+name,{k:str(v) for k,v in attrs.items()})
    root=ET.Element('{'+ns+'}model',{'identifier':'netzero-epa','version':'2.0','{'+xsi+'}schemaLocation':ns+' https://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd'})
    sub(root,'name').text='NetZero Hub NSW EPA enterprise architecture'
    elements=sub(root,'elements')
    for id,typ,name,x,y,w,h in es:
        e=sub(elements,'element',identifier=id,**{'{'+xsi+'}type':typ});sub(e,'name').text=name
    relationships=sub(root,'relationships')
    for i,(typ,source,target) in enumerate(rs):
        kwargs={'identifier':'rel'+str(i),'source':source,'target':target,'{'+xsi+'}type':typ}
        if typ=='Access':kwargs['accessType']='ReadWrite'
        sub(relationships,'relationship',**kwargs)
    views=sub(root,'views');diagrams=sub(views,'diagrams');view=sub(diagrams,'view',identifier='layered-view',**{'{'+xsi+'}type':'Diagram'})
    sub(view,'name').text='Business application and technology layers'
    for id,typ,name,x,y,w,h in es:
        sub(view,'node',identifier='node-'+id,elementRef=id,x=x,y=y,w=w,h=h,**{'{'+xsi+'}type':'Element'})
    for i,(typ,source,target) in enumerate(rs):
        sub(view,'connection',identifier='connection-'+str(i),relationshipRef='rel'+str(i),source='node-'+source,target='node-'+target,**{'{'+xsi+'}type':'Relationship'})
    ET.indent(root);ET.ElementTree(root).write(ROOT/'models'/'NSW_EPA_ArchiMate.xml',encoding='utf-8',xml_declaration=True)
    c=Canvas(2010,1530);c.text(35,38,'D1 Enterprise architecture in ArchiMate',size=29,width=100)
    for y,h,label,fill in [(65,390,'BUSINESS','#fffae9'),(475,585,'APPLICATION','#edf7fc'),(1080,380,'TECHNOLOGY','#f0f8ed')]:
        c.rect(35,y,1940,h,fill=fill);c.text(50,y+26,label,size=22,width=30)
    positions={id:(x,y,w,h) for id,typ,name,x,y,w,h in es}
    for i,(typ,source,target) in enumerate(rs):
        x,y,w,h=positions[source];xx,yy,ww,hh=positions[target]
        if source=='asL' and target=='acUI':
            pts=[(x+w,y+h/2),(755,y+h/2),(755,yy+hh/2),(xx,yy+hh/2)]
        elif source=='asI' and target=='acUI':
            pts=[(x,y+h/2),(1195,y+h/2),(1195,yy+hh/2),(xx+ww,yy+hh/2)]
        elif source=='epa' and target=='roleI':
            pts=[(x+w,y+15),(350,y+15),(350,95),(1350,95),(1350,yy)]
        elif abs(x-xx)<50:
            pts=[(x+w/2,y if y>yy else y+h),(xx+ww/2,yy+hh if y>yy else yy)]
        elif yy>y+150 or y>yy+150:
            pts=[(x+w/2,y if y>yy else y+h),(xx+ww/2,yy+hh if y>yy else yy)]
        else:
            pts=[(x if x>xx else x+w,y+h/2),(xx+ww if x>xx else xx,yy+hh/2)]
        c.line(pts,dashed=typ in ['Realization','Access'],arrow=True,
               marker='triangle' if typ=='Realization' else 'open' if typ in ['Access','Serving'] else 'arrow',
               start='circle' if typ=='Assignment' else 'open' if typ=='Access' else None)
    for id,typ,name,x,y,w,h in es:
        fill='#fff6d5' if typ.startswith('Business') else '#dceff9' if typ.startswith('Application') or typ=='DataObject' else '#e1efd9'
        c.rect(x,y,w,h,fill=fill,rounded=typ in ['BusinessService','ApplicationService','TechnologyService'])
        c.text(x+w/2,y+23,typ,size=18,center=True,width=30)
        c.text(x+w/2,y+h/2+21,name,size=22,center=True,width=int(w/12))
    c.text(40,1490,'Legend: hollow triangle = realization; circle and arrow = assignment; solid open arrow = serving; dotted double arrow = read and write access.',size=21,width=152)
    c.save('D1_ArchiMate_layers')
    (ROOT/'models'/'architecture_catalogue.json').write_text(json.dumps({'elements':es,'relationships':rs},indent=2))

def deployment():
    c=Canvas(1580,1110);c.text(35,38,'E1 React frontend and independent backend services',size=29,width=110)
    c.rect(470,75,640,105,'BROWSER\nReact EPA workspace at /epa',size=25)
    c.line([(790,180),(790,255)])
    c.text(825,222,'Same-origin HTTP requests',size=20,width=42)
    c.rect(385,255,810,145,'WEB DELIVERY AND API PROXY\nLocal Vite on 5173: verified\nOptional Nginx web container on 8080: not executed',size=24)
    c.rect(55,510,550,220,'LICENSING PROCESS\nFastAPI and Uvicorn on port 8001\nP1 applications and P2 variations\nOwn transactions and event table',size=24)
    c.rect(975,510,550,220,'INCIDENT PROCESS\nFastAPI and Uvicorn on port 8002\nP3 reporting and investigation\nOwn transactions and event table',size=24)
    c.line([(590,400),(590,450),(330,450),(330,510)])
    c.line([(990,400),(990,450),(1250,450),(1250,510)])
    c.text(65,473,'/api/v1/epa/licensing',size=22,width=35)
    c.text(1000,430,'/api/v1/epa/incidents',size=22,width=35)
    c.line([(975,580),(605,580)])
    c.text(790,559,'GET licence context',size=20,center=True,width=26)
    c.text(790,645,'2 second timeout\nBackend service token\nRetry after 503',size=20,center=True,width=26)
    c.rect(155,825,350,130,'licensing.sqlite\nCases and licences\nVersion and audit events',fill='#e3efdf',size=23)
    c.rect(1075,825,350,130,'incidents.sqlite\nReports and evidence\nVersion and audit events',fill='#e3efdf',size=23)
    c.line([(330,730),(330,825)],label='owns')
    c.line([(1250,730),(1250,825)],label='owns')
    c.text(45,1010,'The proxy strips each public API prefix. Browser requests never use Docker-only service names.',size=22,width=125)
    c.text(45,1060,'Local Python and Node execution is verified. Compose defines web, licensing and incidents with separate database volumes.',size=22,width=125)
    c.save('E1_Deployment')

if __name__=='__main__':soaml();archimate();deployment();print('Created SoaML, ArchiMate and deployment diagrams')
