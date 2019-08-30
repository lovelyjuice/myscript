import socket
import threading
import argparse
import threadpool

lock = threading.Lock()
ip_dict = dict()
fail_prompt = 'Failed:\t'


def get_domains_from_stdin():
    domain_list = []
    print(r'Input domains, support domains splited by ",", " " and Enter')
    input_content = input().strip()
    if ',' in input_content:
        domain_list.extend(map(lambda x: x.strip(), input_content.split(',')))
    elif ' ' in input_content:
        domain_list = input_content.split(' ')
    else:
        try:
            while input_content != '':
                domain_list.append(input_content)
                input_content = input().strip()
        except EOFError:
            pass
    return domain_list


def get_domains_from_file(filename):
    domain_list = []
    with open(filename, 'r') as f:
        domain_list.extend(map(lambda x: x.strip(), f))
    return domain_list


def get_ip(domain):
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        ip = fail_prompt
    lock.acquire()
    if ip in ip_dict:
        ip_dict[ip].append(domain)
    else:
        ip_dict[ip] = [domain]
    lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--file', help=r'File contains domains, support domains splited by [",", " ", "\n"]')
    parser.add_argument('-s', '--split', default='\n')
    parser.add_argument('domains', nargs='*')
    parser.add_argument('--threads', type=int, default=10)
    args = parser.parse_args()
    if args.file:
        domain_list = get_domains_from_file(args.file)
    else:
        domain_list = args.domains if args.domains else get_domains_from_stdin()
    # resolve
    workers_num = args.threads if args.threads < len(
        domain_list) else len(domain_list)
    pool = threadpool.ThreadPool(workers_num)
    requests = threadpool.makeRequests(get_ip, domain_list)
    [pool.putRequest(request) for request in requests]
    pool.wait()
    for ip in ip_dict:
        if ip != fail_prompt:
            print(f"{ip}\t{','.join(ip_dict[ip])}")
    print(f"{fail_prompt}\t{','.join(ip_dict[fail_prompt])}")
    # print(ip_dict)
    # print(args)
