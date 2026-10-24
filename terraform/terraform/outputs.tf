output "vm_ips" {
  value = { for name, vm in var.vms : name => vm.ip }
}
