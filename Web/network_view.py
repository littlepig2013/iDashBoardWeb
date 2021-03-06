# coding: utf-8
import json
from django.db.models import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from models import Network, NetInterface, Host, VM, MachineInfo
from communication import communicate
from vp_interface import *
from util import *


# @login_required
def network_view(request):
    operation_type = request.POST['operation_type']
    try:
        if operation_type == CREATE_INTNET:
            pass
        elif operation_type == DELETE_INTNET:
            net = Network.objects.get(name=request.POST['net_name'])
            delete_intnet(request.user, net.host, net)
        elif operation_type == ADD_VM_TO_INTNET:
            net = Network.objects.get(name=request.POST['net_name'])
            vm = VM.objects.get(name=request.POST['vm_name'])
            add_vm_to_intnet(request.user, net, vm)

        elif operation_type == CREATE_HOSTONLY:
            host = Host.objects.get(id=int(request.POST['id']))
            create_hostonly(request.user, host, request.POST['ip'], request.POST['netmask'], request.POST['lower_ip'],
                            request.POST['upper_ip'])
        elif operation_type == DELETE_HOSTONLY:
            net = Network.objects.get(name=request.POST['net_name'])
            delete_hostonly(request.user, net.host, net)
        elif operation_type == ADD_VM_TO_HOSTONLY:
            net = Network.objects.get(name=request.POST['net_name'])
            vm = VM.objects.get(name=request.POST['vm_name'])
            add_vm_to_hostonly(request.user, net, vm)

        elif operation_type == REMOVE_VM_FROM_NETWORK:
            net = Network.objects.get(name=request.POST["net_name"])
            vm = VM.objects.get(name=request.POST["vm_name"])
            remove_vm_from_network(request.user, vm, net)
        else:
            pass
    except ObjectDoesNotExist:
        return HttpResponse("Objects Not Found")
    except MultiValueDictKeyError:
        return HttpResponse("Wrong Value")
    return HttpResponse("success")


@login_required
def network_test(request):
    host = Host.objects.get(pk=1)
    # remove_vm_from_intnet(request.user, vm1, network1)
    return HttpResponse("Be happy")


def create_intnet(user, host, net_name, ip, netmask, lower_ip, upper_ip):
    data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                     operation_type=CREATE_INTNET, net_name=net_name,
                     ip=ip, netmask=netmask, lower_ip=lower_ip, upper_ip=upper_ip)

    communicate(data_dict, host.ip, host.vm_manager_port)
    network = Network(name=net_name, type=INTNET, host=host, ip=ip, netmask=netmask, lower_ip=lower_ip,
                      upper_ip=upper_ip, machines=json.dumps([]))
    network.save()


def create_hostonly(user, host, ip, netmask, lower_ip, upper_ip):
    data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                     operation_type=CREATE_HOSTONLY, ip=ip, netmask=netmask, lower_ip=lower_ip, upper_ip=upper_ip)
    response_dict = communicate(data_dict, host.ip, host.vm_manager_port)
    net_name = response_dict["net_name"]
    network = Network(name=net_name, type=HOSTONLY, host=host, ip=ip, netmask=netmask, lower_ip=lower_ip,
                      upper_ip=upper_ip, machines=json.dumps([]))
    network.save()
    return net_name


def delete_intnet(user, host, network):
    cascaded_delete_interface(network)
    data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                     operation_type=DELETE_INTNET, net_name=network.name)
    communicate(data_dict, host.ip, host.vm_manager_port)
    network.delete()


def delete_hostonly(user, host, network):
    cascaded_delete_interface(network)
    data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                     operation_type=DELETE_HOSTONLY, net_name=network.name)
    communicate(data_dict, host.ip, host.vm_manager_port)
    network.delete()


def add_vm_to_intnet(user, network, vm):
    if_code, if_no, vm_interface = set_vm_network(vm, network)
    if if_no > 0:
        print(vm.name)
        data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                         operation_type=ADD_VM_TO_INTNET, net_name=network.name, vm_name=vm.name, if_code=if_code,
                         if_no=if_no)
        communicate(data_dict, vm.host.ip, vm.host.vm_manager_port)
        vm_interface.save()
        machines = json.loads(network.machines)
        machines.append(vm.info_id)
        network.machines = json.dumps(machines)
        network.save()


def add_vm_to_hostonly(user, network, vm):
    if_code, if_no, vm_interface = set_vm_network(vm, network)
    if if_no > 0:
        data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                         operation_type=ADD_VM_TO_HOSTONLY, net_name=network.name, vm_name=vm.name, if_code=if_code,
                         if_no=if_no)
        communicate(data_dict, vm.host.ip, vm.host.vm_manager_port)
        vm_interface.save()
        machines = json.loads(network.machines)
        machines.append(vm.info_id)
        network.machines = json.dumps(machines)
        network.save()


def remove_vm_from_network(user, vm, network):
    # 虚拟机必须是开机状态
    vm_if = NetInterface.objects.get(vm=vm)

    if_no = 0
    if vm_if.eth1_network == network:
        vm_if.eth1_type = NULL
        vm_if.eth1_network = None
        if_no = 1
    elif vm_if.eth2_network == network:
        vm_if.eth2_type = NULL
        vm_if.eth2_network = None
        if_no = 2
    elif vm_if.eth3_network == network:
        vm_if.eth3_type = NULL
        vm_if.eth3_network = None
        if_no = 3
    else:
        # handle an error
        pass
    vm_if.save()
    if_code = calculate_if_code(vm_if)
    machines = json.loads(network.machines)
    machines.remove(vm.info_id)
    network.machines = json.dumps(machines)
    network.save()
    data_dict = dict(request_type="network", request_id=random_str(), request_userid=user.id,
                     operation_type=REMOVE_VM_FROM_NETWORK, net_name=network.name, vm_name=vm.name, if_no=if_no,
                     if_code=if_code)
    communicate(data_dict, vm.host.ip, vm.host.vm_manager_port)
    print(vm.name)


def create_intnet_with_vms_req(request):
    try:
        vms = (request.POST.get('vms', '')).split(',')
        host = VM.objects.get(name=vms[0]).host
        net_type = request.POST.get('net_type', '')
        net_name = request.POST.get('net_name', '')
        net_ip = request.POST.get('net_ip', '')
        net_mask = request.POST.get('net_mask', '')
        lower_ip = request.POST.get('lower_ip', '')
        upper_ip = request.POST.get('upper_ip', '')
        if net_type == 'Internal Network':
            create_intnet(request.user, host, net_name, net_ip, net_mask, lower_ip, upper_ip)
            for vm_name in vms:
                vm = VM.objects.get(name=vm_name)
                network = Network.objects.get(name=net_name)
                add_vm_to_intnet(request.user, network, vm)

        else:
            net_name = create_hostonly(request.user, host, net_ip, net_mask, lower_ip, upper_ip)
            for vm_name in vms:
                vm = VM.objects.get(name=vm_name)
                network = Network.objects.get(name=net_name)
                add_vm_to_hostonly(request.user, network, vm)

        return HttpResponse('Succeed')
    except:
        return HttpResponse('Failed')


def rm_vm_from_networks_req(request):
    try:
        network_ids = (request.POST.get('network_ids', '')).split(',')
        info_id = request.POST.get('info_id', '')
        vm = VM.objects.get(info_id=info_id)
        if vm.state == 'Offline':
            return HttpResponse('Offline')
        print(network_ids)
        for network_id in network_ids:
            print(network_id)
            network = Network.objects.get(id=network_id)
            remove_vm_from_network(request.user, vm, network)
        return HttpResponse('Succeed')
    except:
        return HttpResponse('Failed')


def del_network_req(request):
    try:
        network_id = request.POST.get('network_id', '')
        network = Network.objects.get(id=network_id)
        host = network.host
        if network.type == INTNET:
            delete_intnet(request.user, host, network)
        if network.type == HOSTONLY:
            delete_hostonly(request.user, host, network)
        return HttpResponse('Succeed')
    except:
        return HttpResponse('Failed')


def add_vm_to_intnet_req(request):
    try:
        vm_info_ids = (request.POST.get('vm_info_ids', '')).split(',')
        network_id = request.POST.get('network_id', '')
        network = Network.objects.get(id=network_id)
        offline_vm_names = []
        for vm_info_id in vm_info_ids:
            vm = VM.objects.get(info_id=vm_info_id)
            if vm.state == 'Offline':
                offline_vm_names.append(vm.name)
            else:
                add_vm_to_intnet(request.user, network, vm)
        if not offline_vm_names:
            return HttpResponse('Succeed')
        else:
            return HttpResponse(json.dumps({'offline_vms_name': offline_vm_names}))
    except:
        return HttpResponse('Failed')


def cascaded_delete_interface(network):
    for vm_if in network.eth1_vms.all():
        remove_vm_from_network(vm_if.vm.user, vm_if.vm, vm_if.eth1_network)

    for vm_if in network.eth2_vms.all():
        remove_vm_from_network(vm_if.vm.user, vm_if.vm, vm_if.eth2_network)

    for vm_if in network.eth3_vms.all():
        remove_vm_from_network(vm_if.vm.user, vm_if.vm, vm_if.eth3_network)
