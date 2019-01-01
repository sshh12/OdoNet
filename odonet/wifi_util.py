import subprocess
import re

def scan_networks(device):

    cmd = ['iwlist ' + device + ' scan']

    results = {}
    cur_device = ''

    try:

        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for rline in proc.stdout.readlines():

            line = rline.decode('ascii')

            param_match = re.search(r'([\w\s()]+?)\s?:\s?"?(["\w:.\s()/=]+?)"?\n', line)
            params2_match = re.findall(r'\s*(\w[\w\s]+?)=([\d/]+?)\s+', line)

            if param_match:
                key, value = param_match.group(1), param_match.group(2)
                key = key.lower().strip().replace(' ', '_')
                value = value.strip()
                if key == 'address':
                    cur_device = value
                    results[cur_device] = {}
                else:
                    results[cur_device][key] = value

            if len(params2_match) > 1:
                for match in params2_match:
                    key, value = match
                    key = key.lower().strip().replace(' ', '_')
                    value = value.strip()
                    if key in ['signal_level', 'quality']:
                        x, y = value.split('/')
                        value = int(x) / int(y)
                    results[cur_device][key] = value

    except:
        print('Unable to read iwlist')

    return results
