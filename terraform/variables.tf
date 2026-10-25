variable "pm_endpoint" {
  type = string
}

variable "pm_api_token" {
  type      = string
  sensitive = true
}

variable "node_name" {
  type = string
}

variable "template_id" {
  type    = number
  default = 9000
}

variable "datastore" {
  type    = string
  default = "one-tb-pool"
}

variable "bridge" {
  type    = string
  default = "vmbr0"
}

variable "gateway" {
  type = string
}

variable "dns" {
  type    = string
  default = "8.8.8.8"
}

variable "ssh_public_key" {
  type    = string
  default = "/root/.ssh/id_ed25519.pub"
}

variable "vms" {
  type = map(object({
    vm_id    = number
    ip       = string
    cores    = number
    memory   = number
    disk     = number
    group    = string
  }))

}
