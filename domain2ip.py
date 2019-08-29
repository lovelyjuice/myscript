import socket
import threading

lock = threading.Lock()


def get_domains_from_input():
    domain_list = []
    input_content = input().strip()
    if ' ' in input_content:
        domain_list = input_content.split(' ')
    elif ',' in input_content:
        domain_list.extend(map(lambda x: x.rstrip(), input_content.split(',')))
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
        domain_list.extend(f)
    return domain_list
    
if __name__ == "__main__":
    pass