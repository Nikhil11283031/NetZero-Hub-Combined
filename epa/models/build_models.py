"""Generate editable BPMN 2.0 models, SVG figures and annotation catalogues."""
from pathlib import Path
import json
import textwrap
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from services.domain import TASKS

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'diagrams';OUT.mkdir(exist_ok=True)
NS={'bpmn':'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi':'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc':'http://www.omg.org/spec/DD/20100524/DC','di':'http://www.omg.org/spec/DD/20100524/DI',
    'xsi':'http://www.w3.org/2001/XMLSchema-instance'}
for k,v in NS.items():ET.register_namespace(k,v)
def tag(k,name):return '{'+NS[k]+'}'+name
def child(parent,kind,**attrs):return ET.SubElement(parent,tag('bpmn',kind),{k:str(v) for k,v in attrs.items()})

EFFECTS={
 'A1':('Application is recorded and submitted.','received(a)'),
 'A2':('Completeness is checked; c records the current result.','checked(a) ∧ completeResult(a,c)'),
 'A3':('Further information is requested; the case awaits it.','infoRequested(a) ∧ awaitingInfo(a)'),
 'A4':('Information is recorded; the case returns for checking.','infoReceived(a) ∧ ¬awaitingInfo(a)'),
 'A5':('The incomplete case closes and stops awaiting information.','state(a,incompleteClosed) ∧ ¬awaitingInfo(a)'),
 'A6':('The environmental assessment and its result e are recorded.','envChecked(a) ∧ envResult(a,e)'),
 'A7':('The suitability and consent assessment result f is recorded.','fitChecked(a) ∧ fitResult(a,f)'),
 'A8':('An authorised officer records a reasoned decision d.','decided(a,d) ∧ reasonRecorded(a)'),
 'A9':('A prototype licence is issued for the approved case.','state(a,approved) ∧ ∃l issued(l,a)'),
 'A10':('Refusal is recorded without issuing a licence.','state(a,refused) ∧ ¬∃l issued(l,a)'),
 'A11':('The application outcome is available to its owner.','outcomeAvailable(a)'),
 'V1':('A variation request referencing an existing licence is recorded.','received(v) ∧ refersTo(v,l)'),
 'V2':('Eligibility and licence version are checked; q is the result.','eligibilityChecked(v) ∧ eligibleResult(v,q)'),
 'V3':('The request is marked invalid; licence conditions stay unchanged.','state(v,invalid) ∧ unchanged(l,v)'),
 'V4':('The proposed change is assessed with result e.','changeAssessed(v) ∧ changeResult(v,e)'),
 'V5':('An authorised officer records a reasoned variation decision d.','decided(v,d) ∧ reasonRecorded(v)'),
 'V6':('The approved conditions replace the previous version.','state(v,approved) ∧ varied(l,v) ∧ version(l,k+1)'),
 'V7':('The variation is refused and the licence is unchanged.','state(v,refused) ∧ unchanged(l,v)'),
 'V8':('The variation outcome is available to its owner.','outcomeAvailable(v)'),
 'I1':('A pollution report is recorded.','received(i)'),
 'I2':('Risk r and responsible-authority result j are recorded.','triaged(i) ∧ risk(i,r) ∧ jurisdiction(i,j)'),
 'I3':('Emergency guidance is available; no emergency call is made.','guidance(i,emergency) ∧ state(i,emergencyGuidance)'),
 'I4':('Responsible-authority guidance is recorded, without transmitting data.','guidance(i,referral) ∧ state(i,referred)'),
 'I5':('An investigator is assigned and investigation opens.','assigned(i)'),
 'I6':('Evidence or its documented unavailability is recorded.','evidenceRecorded(i)'),
 'I7':('Licence context, no match or no supplied reference is recorded.','contextRecorded(i)'),
 'I8':('Evidence is evaluated and substantiation result s is recorded.','evaluated(i) ∧ substantiatedResult(i,s)'),
 'I9':('The selected regulatory action is recorded for the case.','actionRecorded(i) ∧ state(i,actionRecorded)'),
 'I10':('A reasoned no-further-action decision is recorded.','noActionRecorded(i) ∧ state(i,noFurtherAction)'),
 'I11':('The investigation is closed.','investigationClosed(i)'),
 'I12':('The permitted incident outcome is available to its owner.','outcomeAvailable(i)'),
}

class Canvas:
    def __init__(self,w,h):
        self.w=w;self.h=h;self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
          '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 Z" fill="#253b50"/></marker><marker id="open" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto-start-reverse"><path d="M0,0 L10,4 L0,8" fill="none" stroke="#253b50"/></marker><marker id="triangle" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto"><path d="M0,0 L12,5 L0,10 Z" fill="white" stroke="#253b50"/></marker><marker id="circle" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><circle cx="4" cy="4" r="3" fill="#253b50"/></marker></defs>',
          '<rect width="100%" height="100%" fill="white"/>']
    def rect(self,x,y,w,h,text='',fill='#f1f6fa',rounded=False,size=21):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{12 if rounded else 0}" fill="{fill}" stroke="#253b50" stroke-width="2"/>')
        if text:self.text(x+w/2,y+h/2,text,size=size,center=True,width=max(8,int(w/(size*.54))))
    def text(self,x,y,text,size=20,center=False,width=40,color='#132f44'):
        lines=[]
        for line in text.split('\n'):
            lines.extend(textwrap.wrap(line,width=width,break_long_words=False,break_on_hyphens=False) or [''])
        yy=y-(len(lines)-1)*size*.62 if center else y
        for i,line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{yy+i*size*1.24}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{"middle" if center else "start"}">{escape(line)}</text>')
    def line(self,points,dashed=False,arrow=True,label=None,marker='arrow',start=None):
        p=' '.join(f'{x},{y}' for x,y in points)
        self.parts.append(f'<polyline points="{p}" fill="none" stroke="#253b50" stroke-width="2.5"'+(' stroke-dasharray="8 6"' if dashed else '')+(f' marker-end="url(#{marker})"' if arrow else '')+(f' marker-start="url(#{start})"' if start else '')+'/>')
        if label:
            p1,p2=max(zip(points,points[1:]),key=lambda pair:abs(pair[0][0]-pair[1][0])+abs(pair[0][1]-pair[1][1]))
            x=(p1[0]+p2[0])/2+8;y=(p1[1]+p2[1])/2-10
            self.parts.append(f'<rect x="{x-3}" y="{y-19}" width="{len(label)*11+8}" height="25" fill="white"/>')
            self.text(x,y,label,size=18,width=20)
    def ellipse(self,x,y,w,h,text='',dashed=False):
        self.parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#f5f9fc" stroke="#253b50" stroke-width="2"'+(' stroke-dasharray="9 6"' if dashed else '')+'/>')
        if text:self.text(x+w/2,y+h/2,text,center=True,width=int(w/11))
    def save(self,name):
        (OUT/(name+'.svg')).write_text('\n'.join(self.parts+['</svg>']))


def node(ident,kind,x,y,w=190,h=100,label=None):
    if kind in ['startEvent','endEvent','boundaryEvent']:w=h=42
    elif 'Gateway' in kind:w=h=48
    return {'id':ident,'kind':kind,'x':x,'y':y,'w':w,'h':h,'label':label or (ident+' '+TASKS[ident][0] if ident in TASKS else '')}


SPECS=[
 {'id':'P1','title':'Licence application','service':'EPA-001','size':(2520,1320),'lane_split':690,
  'nodes':[node('s','startEvent',100,258),node('A1','serviceTask',180,230),node('A2','userTask',440,230),
   node('gComplete','exclusiveGateway',720,256,label='Complete?'),node('A3','sendTask',440,450),
   node('A4','receiveTask',180,450),node('timer','boundaryEvent',315,530),node('A5','serviceTask',180,760),
   node('split','parallelGateway',825,256),node('A6','userTask',940,230),node('A7','userTask',940,460),
   node('join','parallelGateway',1195,256),node('A8','userTask',1310,230),node('gDecision','exclusiveGateway',1585,256,label='Approved?'),
   node('A9','serviceTask',1730,760),node('A10','userTask',1730,460),node('merge','exclusiveGateway',1995,786),
   node('A11','serviceTask',2130,760),node('end','endEvent',2400,789)],
  'edges':[('s','A1',''),('A1','A2',''),('A2','gComplete',''),('gComplete','A3','no'),('A3','A4',''),
   ('A4','A2','recheck'),('timer','A5','30 days'),('gComplete','split','yes'),('split','A6',''),('split','A7',''),
   ('A6','join',''),('A7','join',''),('join','A8',''),('A8','gDecision',''),('gDecision','A9','yes'),
   ('gDecision','A10','no'),('A9','merge',''),('A10','merge',''),('merge','A11',''),('A5','A11','incomplete'),('A11','end','')],
  'cumulative':[('join','C1 Both assessments are available\nBaseA(a) ∧ envChecked(a) ∧ envResult(a,e) ∧ fitChecked(a) ∧ fitResult(a,f)'),
   ('A9','C2 Approval and licence recorded\nC1(a) ∧ decided(a,approve) ∧ reasonRecorded(a) ∧ state(a,approved) ∧ ∃l issued(l,a)'),
   ('A10','C3 Refusal recorded\nC1(a) ∧ decided(a,refuse) ∧ reasonRecorded(a) ∧ state(a,refused) ∧ ¬∃l issued(l,a)')],
  'message_targets':['A1','A4','A3','A11'],'data_target':'A2'},
 {'id':'P2','title':'Licence variation','service':'EPA-001','size':(2250,1180),'lane_split':660,
  'nodes':[node('s','startEvent',100,258),node('V1','serviceTask',180,230),node('V2','userTask',450,230),
   node('gEligible','exclusiveGateway',730,256,label='Eligible?'),node('V3','userTask',450,450),
   node('V4','userTask',850,230),node('V5','userTask',1120,230),node('gDecision','exclusiveGateway',1400,256,label='Approved?'),
   node('V6','serviceTask',1530,730),node('V7','userTask',1530,450),node('merge','exclusiveGateway',1810,756),
   node('V8','serviceTask',1900,730),node('end','endEvent',2160,759)],
  'edges':[('s','V1',''),('V1','V2',''),('V2','gEligible',''),('gEligible','V3','no'),('gEligible','V4','yes'),
   ('V4','V5',''),('V5','gDecision',''),('gDecision','V6','yes'),('gDecision','V7','no'),
   ('V6','merge',''),('V7','merge',''),('V3','V8','invalid'),('merge','V8',''),('V8','end','')],
  'cumulative':[('V4','C4 Change assessed\nBaseV(v,l) ∧ changeAssessed(v) ∧ changeResult(v,e)'),
   ('V6','C5 New licence version recorded\nC4(v,l) ∧ decided(v,approve) ∧ reasonRecorded(v) ∧ state(v,approved) ∧ varied(l,v) ∧ version(l,k+1)'),
   ('V7','C6 Refusal preserves the licence\nC4(v,l) ∧ decided(v,refuse) ∧ reasonRecorded(v) ∧ state(v,refused) ∧ unchanged(l,v)')],
  'message_targets':['V1','V8'],'data_target':'V2'},
 {'id':'P3','title':'Pollution reporting and investigation','service':'EPA-002','size':(2940,1390),'lane_split':760,
  'nodes':[node('s','startEvent',85,258),node('I1','serviceTask',160,230),node('I2','userTask',405,230),
   node('gEmergency','exclusiveGateway',650,256,label='Emergency?'),node('I3','serviceTask',550,485),
   node('gJurisdiction','exclusiveGateway',785,256,label='EPA?'),node('I4','serviceTask',800,650),
   node('I5','userTask',925,230),node('split','parallelGateway',1180,256),
   node('I6','userTask',1300,230),node('I7','userTask',1300,495),node('join','parallelGateway',1570,256),
   node('I8','userTask',1690,230),node('gSubstantiated','exclusiveGateway',1940,256,label='Substantiated?'),
   node('I9','userTask',2080,230),node('I10','userTask',2080,495),node('merge','exclusiveGateway',2330,256),
   node('I11','userTask',2450,230),node('I12','serviceTask',2450,890),node('end','endEvent',2790,919)],
  'edges':[('s','I1',''),('I1','I2',''),('I2','gEmergency',''),('gEmergency','I3','yes'),
   ('gEmergency','gJurisdiction','no'),('gJurisdiction','I4','no'),('gJurisdiction','I5','yes'),
   ('I5','split',''),('split','I6',''),('split','I7',''),('I6','join',''),('I7','join',''),('join','I8',''),
   ('I8','gSubstantiated',''),('gSubstantiated','I9','yes'),('gSubstantiated','I10','no'),
   ('I9','merge',''),('I10','merge',''),('merge','I11',''),('I11','I12',''),('I3','I12','guidance'),
   ('I4','I12','referral'),('I12','end','')],
  'cumulative':[('join','C7 Evidence and context both available\nBaseI(i) ∧ evidenceRecorded(i) ∧ contextRecorded(i)'),
   ('I11','C8 Substantiated investigation closed\nC7(i) ∧ evaluated(i) ∧ substantiatedResult(i,true) ∧ actionRecorded(i) ∧ state(i,actionRecorded) ∧ investigationClosed(i)'),
   ('I4','C9 Referred outside EPA\nreceived(i) ∧ triaged(i) ∧ risk(i,nonEmergency) ∧ jurisdiction(i,other) ∧ guidance(i,referral) ∧ state(i,referred)')],
  'message_targets':['I1','I12'],'data_target':'I6'}]

# Space the tiers so English and logical annotations remain inside their lanes.
SPECS[0]['size']=(2520,1500);SPECS[0]['lane_split']=780
for n in SPECS[0]['nodes']:
    if n['id'] in ['A3','A4']:n['y']=500
    if n['id']=='timer':n['y']=580
    if n['id'] in ['A7','A10']:n['y']=510
    if n['id'] in ['A5','A9','A11']:n['y']=860
    if n['id']=='merge':n['y']=886
    if n['id']=='end':n['y']=889
SPECS[1]['size']=(2250,1410);SPECS[1]['lane_split']=780
for n in SPECS[1]['nodes']:
    if n['id'] in ['V3','V7']:n['y']=520
    if n['id'] in ['V6','V8']:n['y']=850
    if n['id']=='merge':n['y']=876
    if n['id']=='end':n['y']=879
SPECS[2]['size']=(2940,1750);SPECS[2]['lane_split']=1080
for n in SPECS[2]['nodes']:
    if n['id'] in ['I3','I7','I10']:n['y']=530
    if n['id']=='I4':n['y']=790
    if n['id']=='I12':n['y']=1160
    if n['id']=='end':n['y']=1189

# Full scenario triples use the path abbreviations expanded on the indexed pages.
PATHS=[
 [('T0 · (A6 || A7)','{A1 · A2[false]}'),
  ('T0 · (A6 || A7) · A8[approve] · A9','{A1 · A2[false], T0 · (A6 || A7) · A8[refuse]}'),
  ('T0 · (A6 || A7) · A8[refuse] · A10','{A1 · A2[false], T0 · (A6 || A7) · A8[approve]}')],
 [('U','{V1 · V2[false]}'),
  ('U · V5[approve] · V6','{V1 · V2[false], U · V5[refuse]}'),
  ('U · V5[refuse] · V7','{V1 · V2[false], U · V5[approve]}')],
 [('N · (I6 || I7)','{E, R}'),
  ('N · (I6 || I7) · I8[true] · I9 · I11','{E, R, N · (I6 || I7) · I8[false]}'),
  ('R · I4','{E, I1 · I2[nonEmergency,epa]}')]]
for spec,labels in zip(SPECS,PATHS):
    spec['cumulative']=[(ref,txt+'\nL = '+path+'\nX = '+excluded)
                        for (ref,txt),(path,excluded) in zip(spec['cumulative'],labels)]

def route(spec,a,b,label):
    if a['id']=='gDecision' and label=='yes':
        return [(a['x']+a['w']/2,a['y']+a['h']),
                (a['x']+a['w']/2,b['y']+b['h']/2),(b['x'],b['y']+b['h']/2)]
    # Long bypasses travel along a dedicated bottom corridor.
    if (a['id'],b['id']) in [('A5','A11'),('V3','V8'),('I3','I12'),('I4','I12')]:
        corridor=spec['size'][1]-300
        if a['id']=='I3':corridor-=65
        return [(a['x'],a['y']+a['h']/2),(a['x']-45,a['y']+a['h']/2),(a['x']-45,corridor),
                (b['x']+b['w']+45,corridor),(b['x']+b['w']+45,b['y']+75),(b['x']+b['w'],b['y']+75)]
    if a['id']=='A4' and b['id']=='A2':
        return [(a['x'],a['y']+30),(155,a['y']+30),(155,215),(b['x']+b['w']/2,215),(b['x']+b['w']/2,b['y'])]
    if a['id']=='timer':return [(a['x']+42,a['y']+21),(410,a['y']+21),(410,b['y']+50),(b['x']+b['w'],b['y']+50)]
    if a['id']=='I11' and b['id']=='I12':return [(a['x']+a['w'],a['y']+50),(2700,a['y']+50),(2700,b['y']+25),(b['x']+b['w'],b['y']+25)]
    if a['x']+a['w']<=b['x']:
        x1=a['x']+a['w'];y1=a['y']+a['h']/2;x2=b['x'];y2=b['y']+b['h']/2
        if abs(y1-y2)<8:return [(x1,y1),(x2,y2)]
        mid=(x1+x2)/2
        return [(x1,y1),(mid,y1),(mid,y2),(x2,y2)]
    if b['x']+b['w']<=a['x']:
        if b['y']>a['y']:
            return [(a['x']+a['w']/2,a['y']+a['h']),(a['x']+a['w']/2,b['y']+b['h']/2),(b['x']+b['w'],b['y']+b['h']/2)]
        return [(a['x'],a['y']+a['h']/2),(b['x']+b['w'],b['y']+b['h']/2)]
    return [(a['x']+a['w']/2,a['y']+a['h']),(b['x']+b['w']/2,b['y'])]

def make_bpmn(spec):
    pid=spec['id'];W,H=spec['size'];canvas=Canvas(W,H)
    canvas.text(40,36,f'{pid}  {spec["title"]}  |  {spec["service"]}',size=28,width=120)
    canvas.rect(40,70,W-80,70,'Applicant or reporter through NetZero Hub',fill='#e9f0f5',size=23)
    canvas.rect(40,170,W-80,H-430,fill='white')
    canvas.text(650 if pid=='P1' else 65,200,'NSW EPA reference workflow and proposed NetZero Hub support',size=22,width=140)
    canvas.line([(40,spec['lane_split']),(W-40,spec['lane_split'])],arrow=False)
    canvas.text(60,spec['lane_split']-12,'Intake and assessment lane',size=18)
    canvas.text(60,H-277,'Registry and outcome lane',size=18)
    defs=ET.Element(tag('bpmn','definitions'),{'id':pid+'_definitions','targetNamespace':'https://netzero.example/epa',
                      'exporter':'NetZero coursework model generator','exporterVersion':'1.0'})
    for name in ['startMessage','dataMessage']:
        child(defs,'message',id=pid+'_'+name,name=name)
    collab=child(defs,'collaboration',id=pid+'_collaboration')
    child(collab,'participant',id=pid+'_consumer',name='Applicant or reporter through NetZero Hub')
    child(collab,'participant',id=pid+'_epa',name='NSW EPA reference workflow',processRef=pid)
    proc=child(defs,'process',id=pid,name=spec['title'],isExecutable='false')
    child(proc,'documentation').text='Reference-based business model. API implementation covers the selected core. Timeouts and digital integration are project assumptions.'
    lanes=child(proc,'laneSet',id=pid+'_lanes')
    lane1=child(lanes,'lane',id=pid+'_intake',name='Intake and assessment')
    lane2=child(lanes,'lane',id=pid+'_registry',name='Registry and outcome')
    diagram=ET.SubElement(defs,tag('bpmndi','BPMNDiagram'),{'id':pid+'_diagram'})
    plane=ET.SubElement(diagram,tag('bpmndi','BPMNPlane'),{'id':pid+'_plane','bpmnElement':pid+'_collaboration'})
    def shape(ident,x,y,w,h,**attrs):
        el=ET.SubElement(plane,tag('bpmndi','BPMNShape'),{'id':ident+'_di','bpmnElement':ident,**attrs})
        ET.SubElement(el,tag('dc','Bounds'),{k:str(v) for k,v in dict(x=x,y=y,width=w,height=h).items()});return el
    shape(pid+'_consumer',40,70,W-80,70,isHorizontal='true');shape(pid+'_epa',40,170,W-80,H-430,isHorizontal='true')
    shape(pid+'_intake',70,170,W-110,spec['lane_split']-170,isHorizontal='true')
    shape(pid+'_registry',70,spec['lane_split'],W-110,H-260-spec['lane_split'],isHorizontal='true')
    nodes={n['id']:n for n in spec['nodes']}
    objects={}
    for n in spec['nodes']:
        ident=pid+'_'+n['id'];attrs={'id':ident,'name':n['label']}
        if n['kind']=='boundaryEvent':attrs.update(attachedToRef=pid+'_A4',cancelActivity='true')
        el=child(proc,n['kind'],**attrs);objects[n['id']]=el
        if n['id']=='s':child(el,'messageEventDefinition',id=pid+'_start_definition',messageRef=pid+'_startMessage')
        if n['id']=='timer':
            timer=child(el,'timerEventDefinition',id=pid+'_timer_definition')
            child(timer,'timeDuration',**{tag('xsi','type'):'bpmn:tFormalExpression'}).text='P30D'
        child(lane1 if n['y']<spec['lane_split'] else lane2,'flowNodeRef').text=ident
        shape(ident,n['x'],n['y'],n['w'],n['h'])
        x,y,w,h=n['x'],n['y'],n['w'],n['h']
        if n['kind'] in ('startEvent','endEvent','boundaryEvent'):
            canvas.parts.append(f'<circle cx="{x+w/2}" cy="{y+h/2}" r="20" fill="white" stroke="#253b50" stroke-width="{5 if n["kind"]=="endEvent" else 2}"/>')
            if n['id']=='s':canvas.rect(x+10,y+14,22,14,fill='white',size=12);canvas.line([(x+10,y+14),(x+21,y+23),(x+32,y+14)],arrow=False)
            if n['id']=='timer':
                canvas.parts.append(f'<circle cx="{x+21}" cy="{y+21}" r="15" fill="white" stroke="#253b50"/>')
                canvas.line([(x+21,y+9),(x+21,y+21),(x+31,y+24)],arrow=False)
        elif 'Gateway' in n['kind']:
            canvas.parts.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="white" stroke="#253b50" stroke-width="2"/>')
            canvas.text(x+w/2,y+h/2+8,'+' if n['kind']=='parallelGateway' else '×',size=32,center=True)
            if n['label']:canvas.text(x+w/2,y-18,n['label'],size=18,center=True,width=17)
        else:
            canvas.rect(x,y,w,h,n['label'],rounded=True,size=21)
            # Standard BPMN task markers: envelope for send/receive; person for user.
            if n['kind'] in ('sendTask','receiveTask'):
                canvas.parts.append(f'<rect x="{x+8}" y="{y+7}" width="18" height="12" fill="{"#253b50" if n["kind"]=="sendTask" else "white"}" stroke="#253b50"/>')
            elif n['kind']=='userTask':
                canvas.parts.append(f'<circle cx="{x+15}" cy="{y+10}" r="4" fill="none" stroke="#253b50"/><path d="M{x+9},{y+23} L{x+9},{y+18} Q{x+15},{y+11} {x+21},{y+18} L{x+21},{y+23}" fill="none" stroke="#253b50"/>')
            else:canvas.text(x+8,y+22,'⚙',size=18,width=2)
    for i,(source,target,label) in enumerate(spec['edges']):
        ident=f'{pid}_flow_{i}';flow=child(proc,'sequenceFlow',id=ident,sourceRef=pid+'_'+source,targetRef=pid+'_'+target,name=label)
        child(objects[source],'outgoing').text=ident;child(objects[target],'incoming').text=ident
        if nodes[source]['kind']=='exclusiveGateway' and source not in ('merge',):
            child(flow,'conditionExpression',**{tag('xsi','type'):'bpmn:tFormalExpression'}).text=label
        pts=route(spec,nodes[source],nodes[target],label)
        canvas.line(pts,label=label if label not in ('yes','no','30 days') else None)
        if label in ('yes','no'):
            a,b=nodes[source],nodes[target]
            if label=='yes' and source=='gDecision':
                canvas.text(a['x']+a['w']/2+8,a['y']+a['h']+42,label,size=18,width=10)
            else:
                canvas.text(pts[0][0]+9,pts[0][1]+(-14 if b['y']<=a['y'] else 38),label,size=18,width=10)
        if label=='30 days':canvas.text(416,nodes['A5']['y']-22,'30 days',size=18,width=10)
        edge=ET.SubElement(plane,tag('bpmndi','BPMNEdge'),{'id':ident+'_di','bpmnElement':ident})
        for x,y in pts:ET.SubElement(edge,tag('di','waypoint'),{'x':str(x),'y':str(y)})
    for n in spec['nodes']:
        if n['id'] not in EFFECTS:continue
        eng,fol=EFFECTS[n['id']];ident=pid+'_effect_'+n['id']
        text=f'{n["id"]} immediate\n{eng}\n{fol}'
        ann=child(proc,'textAnnotation',id=ident);child(ann,'text').text=text
        assoc=child(proc,'association',id=ident+'_assoc',sourceRef=pid+'_'+n['id'],targetRef=ident)
        # Effects sit below each task; full English remains in editable BPMN and catalogue.
        ax,ay=n['x'],n['y']+n['h']+30
        display=fol
        canvas.text(ax,ay,display,size=18,width=27,color='#315c42')
        canvas.text(ax,ay+70,eng,size=15,width=32,color='#486252')
        shape(ident,ax,ay-15,230,115)
        ed=ET.SubElement(plane,tag('bpmndi','BPMNEdge'),{'id':ident+'_assoc_di','bpmnElement':ident+'_assoc'})
        for xx,yy in [(n['x']+n['w']/2,n['y']+n['h']),(ax+100,ay-15)]:ET.SubElement(ed,tag('di','waypoint'),{'x':str(xx),'y':str(yy)})
    # Cumulative effect summaries appear as annotations on the model itself.
    cw=(W-120)/3
    for i,(ref,text) in enumerate(spec['cumulative']):
        ax=50+i*cw;ay=H-210;ident=pid+'_cum_'+str(i)
        ann=child(proc,'textAnnotation',id=ident);child(ann,'text').text=text
        child(proc,'association',id=ident+'_assoc',sourceRef=pid+'_'+ref,targetRef=ident)
        shape(ident,ax,ay,cw-20,190)
        canvas.rect(ax,ay,cw-20,190,fill='#f0f7f0')
        canvas.text(ax+12,ay+26,text,size=18,width=int((cw-44)/10))
        ed=ET.SubElement(plane,tag('bpmndi','BPMNEdge'),{'id':ident+'_assoc_di','bpmnElement':ident+'_assoc'})
        n=nodes[ref]
        for xx,yy in [(n['x']+n['w']/2,n['y']+n['h']),(ax+cw/2,ay)]:ET.SubElement(ed,tag('di','waypoint'),{'x':str(xx),'y':str(yy)})
    # Consumer is black box; only message flows cross the pool boundary.
    for i,ref in enumerate(spec['message_targets']):
        n=nodes[ref];outgoing=ref in ['A3','A11','V8','I12']
        initial=ref in ['A1','V1','I1']
        src=pid+'_'+ref if outgoing else pid+'_consumer';dst=pid+'_consumer' if outgoing else pid+('_s' if initial else '_'+ref)
        ident=pid+'_message_'+str(i);child(collab,'messageFlow',id=ident,sourceRef=src,targetRef=dst,name='request or outcome')
        target=nodes['s'] if initial else n
        pts=[(target['x']+target['w']/2,140),(target['x']+target['w']/2,target['y'])]
        if outgoing:
            pts=[(n['x']+n['w'],n['y']+12),(W-60,n['y']+12),(W-60,140)]
        ed=ET.SubElement(plane,tag('bpmndi','BPMNEdge'),{'id':ident+'_di','bpmnElement':ident})
        for x,y in pts:ET.SubElement(ed,tag('di','waypoint'),{'x':str(x),'y':str(y)})
        # To keep the published figure clear, draw the initial request and final outcome.
        if ref in ['A1','V1','I1','A11','V8','I12']:canvas.line(pts,dashed=True)
    # Data object and a dotted association are kept separate from control flow.
    obj=child(proc,'dataObject',id=pid+'_data');dref=child(proc,'dataObjectReference',id=pid+'_data_ref',dataObjectRef=pid+'_data',name='Case documents')
    dx=W-230;dy=175;shape(pid+'_data_ref',dx,dy,90,65)
    canvas.rect(dx,dy,90,65,'Case\ndata',fill='#fff8e2',size=19)
    assoc=child(proc,'association',id=pid+'_data_assoc',sourceRef=pid+'_data_ref',targetRef=pid+'_'+spec['data_target'])
    target=nodes[spec['data_target']]
    canvas.line([(dx,dy+32),(dx-18,dy+32),(dx-18,212),(target['x']+target['w']/2,212),(target['x']+target['w']/2,target['y'])],dashed=True,arrow=False)
    ed=ET.SubElement(plane,tag('bpmndi','BPMNEdge'),{'id':pid+'_data_assoc_di','bpmnElement':pid+'_data_assoc'})
    for x,y in [(dx,dy+32),(target['x']+target['w']/2,target['y'])]:ET.SubElement(ed,tag('di','waypoint'),{'x':str(x),'y':str(y)})
    # Incoming/outgoing must precede task/event-specific children in BPMN XSD.
    for el in objects.values():
        children=list(el);rank={'documentation':0,'incoming':1,'outgoing':2}
        children.sort(key=lambda c:rank.get(c.tag.split('}')[-1],3));el[:]=children
    # BPMN process content order: documentation, lanes, flow elements, artifacts.
    proc[:]=sorted(list(proc),key=lambda c: {'documentation':0,'laneSet':1,'textAnnotation':3,'association':3}.get(c.tag.split('}')[-1],2))
    ET.indent(defs);ET.ElementTree(defs).write(ROOT/'models'/(pid+'.bpmn'),encoding='utf-8',xml_declaration=True)
    canvas.save(pid+'_BPMN')


def main():
    for spec in SPECS:make_bpmn(spec)
    (ROOT/'models'/'effects.json').write_text(json.dumps({k:{'task':TASKS[k][0],'english':v[0],'fol':v[1]} for k,v in EFFECTS.items()},indent=2,ensure_ascii=False))
    (ROOT/'models'/'process_catalogue.json').write_text(json.dumps(SPECS,indent=2,ensure_ascii=False))
    print('Created P1, P2 and P3 BPMN models and effect catalogue')

if __name__=='__main__':main()
