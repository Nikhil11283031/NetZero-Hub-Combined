"""Execute the same business transitions used by the APIs with a seeded clock.

The durations and branch probabilities are academic assumptions, not EPA data.
The simulator runs business commands locally; demo.py separately verifies HTTP.
"""
import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from services.domain import TASKS, transition

# Mean active hours and mean waiting hours before a task starts.
TIMES={
 'A1':(.1,0),'A2':(1,6),'A3':(.3,0),'A4':(.5,48),'A5':(.1,720),
 'A6':(10,48),'A7':(4,48),'A8':(1,16),'A9':(.2,0),'A10':(.2,0),'A11':(.1,0),
 'V1':(.1,0),'V2':(.5,4),'V3':(.1,0),'V4':(6,24),'V5':(.5,8),'V6':(.2,0),'V7':(.2,0),'V8':(.1,0),
 'I1':(.1,0),'I2':(.5,1),'I3':(.05,0),'I4':(.2,0),'I5':(.2,4),
 'I6':(12,18),'I7':(1,24),'I8':(4,12),'I9':(1,2),'I10':(.2,0),'I11':(.2,0),'I12':(.1,0),
}


class Execution:
    def __init__(self,case,rng,start):
        self.case=case;self.rng=rng;self.clock=start;self.rows=[]
        self.emit([{'P1':'A1','P2':'V1','P3':'I1'}[case['process']]])

    def emit(self,ids):
        for task in ids:
            active,wait=TIMES[task]
            wait=720 if task=='A5' else wait*self.rng.uniform(.7,1.3)
            # A5's timer is measured from A3 completion, with no intervening work.
            start=self.clock+timedelta(hours=wait)
            end=start+timedelta(hours=active*self.rng.uniform(.75,1.25))
            label,resource=TASKS[task]
            self.rows.append({'case_id':self.case['id'],'process':self.case['process'],
                'task_id':task,'activity':label,'start_timestamp':start.isoformat(),
                'timestamp':end.isoformat(),'resource':resource,'lifecycle':'complete',
                'active_hours':(end-start).total_seconds()/3600,'wait_hours':wait})
            self.clock=end

    def do(self,action,**values):
        self.case,ids=transition(self.case,action,values);self.emit(ids)

    def parallel(self,commands):
        start=self.clock;ends=[]
        for action,values in commands:
            self.clock=start;self.do(action,**values);ends.append(self.clock)
        self.clock=max(ends)


def simulate(n=100,seed=927,output=Path('results')):
    rng=random.Random(seed);rows=[];cases=[]
    for process in ('P1','P2','P3'):
        for number in range(n):
            base={'id':f'{process}-{number+1:04d}','process':process,'owner':'simulated-client',
                  'state':'SUBMITTED','version':1,'data':{}}
            if process=='P1':
                incomplete=rng.random()<.35
                base['data']={'documents':[] if incomplete else ['site-plan.pdf'],
                             'fee_reference':'SIM-FEE','consent_reference':'SIM-CONSENT'}
                ex=Execution(base,rng,datetime(2026,9,1,tzinfo=timezone.utc)+timedelta(hours=number*6))
                ex.do('check')
                if incomplete:
                    if rng.random()<.15:
                        ex.do('expire',rationale='Simulated 30 day information deadline elapsed')
                    else:
                        # Some cases undergo a second information round.
                        if rng.random()<.2:
                            ex.do('supply',documents=[]);ex.do('check')
                        ex.do('supply',documents=['site-plan.pdf']);ex.do('check')
                if ex.case['state']=='ASSESSMENT':
                    env=rng.random()>.15;suit=rng.random()>.08
                    ex.parallel([('assess_environment',{'passed':env,'rationale':'Simulated assessment'}),
                                 ('assess_suitability',{'passed':suit,'rationale':'Simulated assessment'})])
                    ex.do('decide',approved=env and suit,rationale='Simulated decision')
            elif process=='P2':
                base['data']={'licence_id':f'NZ-SIM-{number}','proposed_conditions':['Simulation only']}
                ex=Execution(base,rng,datetime(2026,9,1,tzinfo=timezone.utc)+timedelta(hours=number*6))
                ex.do('verify',eligible=rng.random()>.12)
                if ex.case['state']=='ASSESSMENT':
                    passed=rng.random()>.2
                    ex.do('assess',passed=passed,rationale='Simulated assessment')
                    ex.do('decide',approved=passed,rationale='Simulated decision')
            else:
                ex=Execution(base,rng,datetime(2026,9,1,tzinfo=timezone.utc)+timedelta(hours=number*6))
                pick=rng.random()
                ex.do('triage',emergency=pick<.1,epa_jurisdiction=pick>=.3)
                if ex.case['state']=='INVESTIGATION':
                    ex.parallel([('collect_evidence',{'summary':'Simulated evidence collection'}),
                                 ('review_licence',{'summary':'Simulated licence context'})])
                    ex.do('conclude',substantiated=rng.random()<.6,rationale='Simulated investigation outcome')
            ex.rows.sort(key=lambda r:(r['timestamp'],r['task_id']))
            for i,row in enumerate(ex.rows,1):
                row['event_index']=i;row['outcome']=ex.case['state'];rows.append(row)
            cases.append({'case_id':ex.case['id'],'process':process,'outcome':ex.case['state']})
    output.mkdir(parents=True,exist_ok=True)
    with (output/'event_log.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'simulation.json').write_text(json.dumps({'seed':seed,'cases_per_process':n,'total_cases':len(cases),
        'total_events':len(rows),'source':'seeded business-transition simulation; no observed EPA data',
        'time_unit':'hours','duration_assumptions':TIMES,
        'branch_assumptions':{'P1_incomplete':.35,'P1_timeout_given_incomplete':.15,
                             'P1_second_information_round_given_response':.2,
                             'P2_ineligible':.12,'P3_emergency':.1,'P3_referral':.2},
        'cases':cases},indent=2))
    print(json.dumps({'cases':len(cases),'events':len(rows),'seed':seed}))
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cases',type=int,default=100)
    parser.add_argument('--seed',type=int,default=927);parser.add_argument('--output',type=Path,default=Path('results'))
    args=parser.parse_args()
    if args.cases<1:parser.error('--cases must be positive')
    simulate(args.cases,args.seed,args.output)
