"""Reference Petri nets transcribed from the BPMN control flow, independent of logs.

These nets check task ordering/joins, not data guards, legal conditions or time.
The P1 boundary timer is represented as the alternative A5 transition.
"""
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils.petri_utils import add_arc_from_to

def build(process):
    net=PetriNet(process+'_reference');places={};transitions={}
    def p(name):
        if name not in places:
            places[name]=PetriNet.Place(name);net.places.add(places[name])
        return places[name]
    def t(name,label=None):
        if name not in transitions:
            transitions[name]=PetriNet.Transition(name,label if label is not None else (None if name.startswith('tau') else name))
            net.transitions.add(transitions[name])
        return transitions[name]
    def step(inputs,name,outputs):
        for place in inputs.split():add_arc_from_to(p(place),t(name),net)
        for place in outputs.split():add_arc_from_to(t(name),p(place),net)
    if process=='P1':
        for args in [('start','A1','received'),('received','A2','checked'),('checked','A3','waiting'),
            ('waiting','A4','received'),('waiting','A5','result'),('checked','tau_complete','env_in fit_in'),
            ('env_in','A6','env_done'),('fit_in','A7','fit_done'),('env_done fit_done','A8','decision'),
            ('decision','A9','result'),('decision','A10','result'),('result','A11','end')]:step(*args)
    elif process=='P2':
        for args in [('start','V1','received'),('received','V2','checked'),('checked','V3','result'),
            ('checked','V4','assessed'),('assessed','V5','decision'),('decision','V6','result'),
            ('decision','V7','result'),('result','V8','end')]:step(*args)
    else:
        for args in [('start','I1','received'),('received','I2','triaged'),('triaged','I3','result'),
            ('triaged','I4','result'),('triaged','I5','evidence_in context_in'),('evidence_in','I6','evidence_done'),
            ('context_in','I7','context_done'),('evidence_done context_done','I8','assessed'),
            ('assessed','I9','conclusion'),('assessed','I10','conclusion'),('conclusion','I11','result'),
            ('result','I12','end')]:step(*args)
    return net,Marking({p('start'):1}),Marking({p('end'):1})
