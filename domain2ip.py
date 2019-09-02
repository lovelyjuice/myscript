import argparse
import socket
import threading

import threadpool

lock = threading.Lock()
ip_dict = dict()
fail_prompt = 'Failed:\t'


def get_domains_from_stdin():
    domain_set = set()
    print(r'Input domains, support domains splited by ",", " " and Enter')
    input_content = input().strip()
    if ',' in input_content:
        domain_set.update(map(lambda x: x.strip(), input_content.split(',')))
    elif ' ' in input_content:
        domain_set = set(input_content.split(' '))
    else:
        try:
            while input_content != '':
                domain_set.add(input_content)
                input_content = input().strip()
        except EOFError:
            pass
    return list(domain_set)


def get_domains_from_file(filename):
    domain_set = set()
    with open(filename, 'r') as f:
        domain_set.update(map(lambda x: x.strip(), f))
    return list(domain_set)


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
        '-f', '--file', help=r'包含域名列表的文件，每个域名之间可用以下字符分隔 [",", " ", "\n", "\r\n"]')
    parser.add_argument('-s', '--split', default=' ',help='分隔符用于分隔解析到的所有IP，默认为空格，分隔符仅在指定--no-domain选项时生效。')
    parser.add_argument('domains', nargs='*',help='域名列表。通过参数传递域名列表，以空格分隔。仅在未指定--file选项时生效。')
    parser.add_argument('--threads', type=int, default=10,help='最大线程数。')
    parser.add_argument('--no-domain', action='store_true',help='不输出IP所对应的域名。')
    args = parser.parse_args()
    if args.file:
        domain_list = get_domains_from_file(args.file)
    else:
        domain_list = list(set(args.domains)) if args.domains else get_domains_from_stdin()
    # resolve domain name
    workers_num = args.threads if args.threads < len(domain_list) else len(domain_list)
    pool = threadpool.ThreadPool(workers_num)
    requests = threadpool.makeRequests(get_ip, domain_list)
    [pool.putRequest(request) for request in requests]
    pool.wait()
    counter = 0
    for ip in ip_dict:
        if ip != fail_prompt:
            if args.no_domain:
                if counter == len(ip_dict) - 2:
                    print(f"{ip}", end='')
                else:
                    print(f"{ip}", end=args.split)
            else:
                print(f"{ip}\t{','.join(ip_dict[ip])}")
            counter += 1
    if fail_prompt in ip_dict and not args.no_domain:
        print(f"{fail_prompt}\t{','.join(ip_dict[fail_prompt])}")
    # print(ip_dict)
    # print(args)
