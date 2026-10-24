import urllib.request
import json
import time
import os

def test():
    # 1. Login
    login_data = json.dumps({'email': 'admin@trafficsense.gov', 'password': 'Admin@123456'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
    resp = json.loads(urllib.request.urlopen(req).read().decode())
    token = resp['access_token']
    print('Authenticated. Token obtained.')

    # 2. Upload video
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    file_path = 'samples/cctv_junction_720p.mp4'
    filename = os.path.basename(file_path)

    body = []
    body.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: video/mp4\r\n\r\n'.encode('utf-8'))
    with open(file_path, 'rb') as f:
        body.append(f.read())
    body.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
    body_bytes = b''.join(body)

    upload_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/videos/analyze',
        data=body_bytes,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
    )
    upload_res = json.loads(urllib.request.urlopen(upload_req).read().decode())
    job_id = upload_res['job_id']
    print(f'Job started: {job_id}')

    # 3. Poll job
    for i in range(40):
        time.sleep(2)
        poll_req = urllib.request.Request(
            f'http://127.0.0.1:8000/api/videos/jobs/{job_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        status = json.loads(urllib.request.urlopen(poll_req).read().decode())
        print(f'Step {i+1}: Status={status["status"]}, Progress={status.get("progress", 0)}%, Violations={len(status.get("violations", []))}')
        if status['status'] in ['completed', 'failed']:
            print('Job finished. Final status:', status['status'])
            print(f'Total violations detected: {len(status.get("violations", []))}')
            break

if __name__ == '__main__':
    test()
