# -*- mode: ruby -*-
# vi: set ft=ruby :

# Stripped-down Vagrantfile for development


# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

MEM = 1024
VCPU = 2
NET = "192.168.10."

HOSTS = {
  "one" => [NET + "200", MEM, VCPU, 0, true],
  "two" => [NET + "201", MEM, VCPU, 1, false]
}

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # Multi-machine configuration: we are configuring two VMs here, so
  # we can easily test two email accounts on the same machine. One VM's
  # sync-engine will listen on port 5555 and the other on port 5556.
  #  - https://github.com/debops/examples/blob/master/vagrant-multi-machine/Vagrantfile
  #  - https://docs.vagrantup.com/v2/multi-machine/
  HOSTS.each do | (name, cfg) |
    ipaddr, mem, vcpu, idx, primary = cfg

    config.vm.define name, primary: primary, autostart: primary do |machine|
      machine.vm.box = "precise64"
      machine.vm.box_url = "http://files.vagrantup.com/precise64.box"
      machine.vm.box_download_checksum_type = "sha256"
      machine.vm.box_download_checksum = "9a8bdea70e1d35c1d7733f587c34af07491872f2832f0bc5f875b536520ec17e"

      machine.vm.provider :virtualbox do |vbox, override|
        vbox.memory = mem
        vbox.cpus = vcpu
      end

      machine.vm.provider :vmware_fusion do |vmware, override|
        override.vm.box = "precise64_fusion"
        override.vm.box_url = "http://files.vagrantup.com/precise64_vmware_fusion.box"
        override.vm.box_download_checksum_type = "sha256"
        override.vm.box_download_checksum = "b79e900774b6a27500243d28bd9b1770e428faa3d8a3e45997f2a939b2b63570"
        vmware.vmx["memsize"] = "#{mem}"
        vmware.vmx["numvcpus"] = "#{vcpu}"
      end

      machine.vm.hostname = "nylas-#{idx}"
      machine.ssh.forward_agent = true

      # machine.vm.customize [
      #   'modifyvm', :id,
      #   "--natdnshostresolver1", "on",
      #   "--natdnsproxy1", "on",
      # ]
      machine.vm.network "private_network", ip: ipaddr
      machine.vm.provision :shell, :inline => "apt-get update -q && cd /vagrant && ./setup.sh"

      # XXX: Not sure why these ports were forwarded in the original Vagrantfile.
      # Leaving them commented until I know.
      # Share ports 5000 - 5008
      #9.times do |n|
      #  machine.vm.network "forwarded_port", guest: 5000+n, host: 5000+n, host_ip: "127.0.0.1"
      #end

      # XXX: Not sure why this port was forwarded in the original Vagrantfile.
      #machine.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1"

      # forwards the sync engine port 5555 so that it can be accessed by remote
      # clients. we need this for our demo.
      machine.vm.network "forwarded_port", guest: 5555+idx, host: 5555+idx, host_ip: "0.0.0.0"
      # forwards UDP port 9000 for the DHT node running in the VM
      machine.vm.network "forwarded_port", guest: 9000+idx, host: 9000+idx, protocol: "udp"
      # ElasticSearch port
      machine.vm.network "forwarded_port", guest: 9200+idx, host: 9200+idx, host_ip: "127.0.0.1"

      # This will share any folder in the parent directory that
      # has the name share-*
      # It mounts it at the root without the 'share-' prefix
      share_prefix = "share-"
      Dir['../*/'].each do |fname|
        basename = File.basename(fname)
        if basename.start_with?(share_prefix)
          mount_path = "/" + basename[share_prefix.length..-1]
          puts "Mounting share for #{fname} at #{mount_path}"
          machine.vm.synced_folder fname, mount_path
        end
      end

      # See: https://stackoverflow.com/questions/14715678/vagrant-insecure-by-default
      unless Vagrant.has_plugin?("vagrant-rekey-ssh")
        warn "------------------- SECURITY WARNING -------------------"
        warn "Vagrant is insecure by default.  To secure your VM, run:"
        warn "    vagrant plugin install vagrant-rekey-ssh"
        warn "--------------------------------------------------------"
      end
    end   # end of config.vm.define name
  end   # end of HOSTS.each do
end   # end of Vagrant.configure

# Local Vagrantfile overrides.  See Vagrantfile.local.example for examples.
Dir.glob('Vagrantfile.local.d/*').sort.each do |path|
  load path
end
Dir.glob('Vagrantfile.local').sort.each do |path|
  load path
end
