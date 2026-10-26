resource "proxmox_virtual_environment_vm" "vm" {
  for_each = var.vms

  name      = each.key
  node_name = var.node_name
  vm_id     = each.value.vm_id

  clone {
    vm_id        = var.template_id
    full         = true
    datastore_id = var.datastore
  }

  agent {
    enabled = false
  }

  cpu {
    cores = each.value.cores
    # x86-64-v3 = v2 + AVX/AVX2/FMA: без AVX колесо paddlepaddle (OCR в source-service) падает
    # с SIGILL «invalid opcode» и роняет сервис. Требует AVX2 у CPU хоста Proxmox (Intel Haswell+/любой Ryzen).
    type  = "x86-64-v3"
  }

  memory {
    dedicated = each.value.memory
  }

  disk {
    datastore_id = var.datastore
    interface    = "scsi0"
    size         = each.value.disk
  }

  network_device {
    bridge = var.bridge
  }

  operating_system {
    type = "l26"
  }

  initialization {
    datastore_id = var.datastore

    ip_config {
      ipv4 {
        address = "${each.value.ip}/24"
        gateway = var.gateway
      }
    }

    dns {
      servers = [var.dns]
    }

    user_account {
      username = "ansible"
      keys     = [trimspace(file(var.ssh_public_key))]
    }
  }
}

resource "local_file" "ansible_inventory" {
  filename = "${path.module}/../ansible/inventory.ini"
  content = templatefile("${path.module}/inventory.tftpl", {
    vms = var.vms
  })
}
