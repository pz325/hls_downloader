import requests
import os
import zmq
from multiprocessing import Process

SERVER_PORTS = [5550]
CLIENT = None


def download(uri, filename):
    '''
    download from uri and save as filename (relative to CWD)
    @param uri
    @param filename
    '''
    resp = requests.get(uri, verify=False)
    with open(filename, 'wb') as f:
        f.write(resp.content)


def download_uri(uri, local, clear_local=False):
    '''
    Download resource from uri, save to local, i.e. path/to/target.file (relative to CWD)

    @param uri Full URI of the target
    @param local path/to/target.file
    '''
    print('downloading {uri} to {local}'.format(uri=uri, local=local))
    if os.path.exists(local):
        if clear_local:
            os.remove(local)
        else:
            print('{local} exists'.format(local=local))
            return

    target_name = os.path.basename(local)
    subfolder = os.path.dirname(local)
    if subfolder and not os.path.exists(subfolder):
        os.makedirs(subfolder)

    download(uri, target_name)
    try:
        os.rename(target_name, local)
    except WindowsError:
        print('Error: exception while moving {filename}'.format(filename=target_name))


def download_uri_async(uri, local, clear_local=False):
    subfolder = os.path.dirname(local)
    if subfolder and not os.path.exists(subfolder):
        os.makedirs(subfolder)
    work_message = {
        'cmd': 'download',
        'uri': uri,
        'local': local,
        'clear_local': False
    }
    global CLIENT
    if not CLIENT:
        CLIENT = get_client()
    CLIENT.send_json(work_message)


def worker(port='5556'):
    '''
    message: {'cmd': 'stop'}
    message: {'cmd': 'download', 'uri': 'uri', 'local': 'local', 'clear_local': False}
    '''
    print('[worker {port}] starts'.format(port=port))
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind('tcp://*:{port}'.format(port=port))
    while True:
        # Wait for next request from client
        message = socket.recv_json()
        print('[worker {port}] message: {message}'.format(port=port, message=message))
        if 'cmd' not in message:
            print('[worker {port}] Error: unsupported message'.format(port=port))
            break

        if message['cmd'] == 'stop':
            break
        elif message['cmd'] == 'download':
            pass
            download_uri(message['uri'], message['local'], message['clear_local'])
        else:
            print('[worker {port}] Error: unsupported cmd'.format(port=port))

    print('[worker {port}] exits'.format(port=port))


def stop_all_workers():
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    for port in SERVER_PORTS:
        socket.connect('tcp://localhost:{port}'.format(port=port))
    for port in SERVER_PORTS:
        socket.send_json({'cmd': 'stop'})


def start_workers(num_workers=4):
    global SERVER_PORTS
    SERVER_PORTS = []
    for n in range(num_workers):
        port = 5550 + n
        SERVER_PORTS.append(port)
        Process(target=worker, args=(port,)).start()
    global CLIENT
    CLIENT = None


def get_client():
    global CLIENT
    if CLIENT:
        return CLIENT

    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.hwm = 1000000
    for port in SERVER_PORTS:
        socket.connect('tcp://localhost:{port}'.format(port=port))
    CLIENT = socket
    return CLIENT


def start(num_workers):
    start_workers(num_workers)


def stop():
    stop_all_workers()


def main():
    start(4)
    client = get_client()

    uri = 'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8'
    local = 'bipbop_4x3/bipbop_4x3_variant.m3u8'

    work_message = {
        'cmd': 'download',
        'uri': uri,
        'local': local,
        'clear_local': False
    }
    client.send_json(work_message)

    stop()


if __name__ == '__main__':
    main()
