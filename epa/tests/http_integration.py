"""Start both services with isolated databases and exercise real HTTP composition."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import httpx

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]

def main():
    with tempfile.TemporaryDirectory() as temp:
        ports=[free_port(),free_port()];procs=[];handles=[]
        bases=[f'http://127.0.0.1:{port}' for port in ports]
        env={**os.environ,'NZ_LICENCE_DB':temp+'/licence.sqlite','NZ_INCIDENT_DB':temp+'/incident.sqlite',
             'NZ_LICENCE_URL':bases[0],'NZ_DEMO_LICENCE_URL':bases[0],'NZ_DEMO_INCIDENT_URL':bases[1]}
        try:
            for module,port in zip(['licensing','incidents'],ports):
                handle=open(temp+'/'+module+'.log','w');handles.append(handle)
                procs.append(subprocess.Popen([sys.executable,'-m','uvicorn',f'services.{module}:create_app',
                    '--factory','--host','127.0.0.1','--port',str(port)],env=env,stdout=handle,stderr=handle))
            for base in bases:
                for attempt in range(100):
                    try:
                        if httpx.get(base+'/health',trust_env=False,timeout=.5).status_code==200:break
                    except httpx.HTTPError:pass
                    if any(p.poll() is not None for p in procs):raise RuntimeError('A service exited before startup')
                    time.sleep(.05)
                else:raise RuntimeError('Service did not start within five seconds')
            subprocess.run([sys.executable,'demo.py'],env=env,check=True)
            Path('docs').mkdir(exist_ok=True)
            for name,base in zip(['licensing','incidents'],bases):
                spec=httpx.get(base+'/openapi.json',trust_env=False).json()
                Path('docs',name+'_openapi.json').write_text(json.dumps(spec,indent=2))
        finally:
            for p in procs:p.terminate()
            for p in procs:p.wait()
            for f in handles:f.close()

if __name__=='__main__':main()
