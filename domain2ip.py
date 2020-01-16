import argparse
import socket
import threading

import threadpool

lock = threading.Lock()
lock2 = threading.Lock()
ip_dict = dict()
fail_prompt = 'Fail to resolve'
failed_times = 0
resolved_num = 0

def printProgress(iteration, total, prefix='', suffix='', decimals=1, barLength=100):
    """
    Call in a loop to create a terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    import sys
    formatStr = "{0:." + str(decimals) + "f}"
    percent = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = '#' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' %
                     (prefix, bar, percent, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


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
        domain_set.update(map(lambda x: x.strip(), f.readlines()))
    return list(domain_set)


def get_ip(domain):
    global failed_times
    global resolved_num
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        ip = fail_prompt
        lock2.acquire()
        failed_times += 1
        lock2.release()
    lock.acquire()
    if ip in ip_dict:
        ip_dict[ip].append(domain)
    else:
        ip_dict[ip] = [domain]
    resolved_num+=1
    printProgress(resolved_num,total_domains_num,'Progress: ','Complete',barLength=50)
    lock.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--file', help=r'包含域名列表的文件，每个域名之间可用以下字符分隔 ["\n", "\r\n"]')
    parser.add_argument('-s', '--split', default=' ',
                        help='分隔符用于分隔解析到的所有IP，默认为空格，分隔符仅在指定--no-domain选项时生效。')
    parser.add_argument('domains', nargs='*',
                        help='域名列表。通过参数传递域名列表，以空格分隔。仅在未指定--file选项时生效。')
    parser.add_argument('--threads', type=int, default=10, help='最大线程数。')
    parser.add_argument('--no-domain', action='store_true',
                        help='不输出IP所对应的域名。')
    args = parser.parse_args()
    if args.file:
        domain_list = get_domains_from_file(args.file)
    else:
        domain_list = list(
            set(args.domains)) if args.domains else get_domains_from_stdin()
    # resolve domain name
    resolved_num, total_domains_num = 0, len(domain_list)
    print(f'Total domains: {total_domains_num}')
    workers_num = args.threads if args.threads < len(
        domain_list) else len(domain_list)
    pool = threadpool.ThreadPool(workers_num)
    requests = threadpool.makeRequests(get_ip, domain_list)
    [pool.putRequest(request) for request in requests]
    pool.wait()
    counter = 0
    for ip in ip_dict:
        if ip != fail_prompt:
            if args.no_domain:
                # 根据ip中是否存在解析失败的项目bool(failed_times)，来确定字典中哪个元素是最后输出的，最后输出的元素（ip地址）不能用args.split结尾，
                # 尤其是args.split 是逗号等非空字符时
                if counter == len(ip_dict) - bool(failed_times) - 1:
                    print(f"{ip}", end='')
                else:
                    print(f"{ip}", end=args.split)
            else:
                print(f"{ip}\t{','.join(ip_dict[ip])}")
            counter += 1
    if fail_prompt in ip_dict and not args.no_domain:
        print(f"[!] {fail_prompt} {len(ip_dict[fail_prompt])} domains:\t{','.join(ip_dict[fail_prompt])}")
    print(f'[*] Total domains: {total_domains_num}')
    print(f'[*] Total IP : {len(ip_dict)-bool(failed_times)}')