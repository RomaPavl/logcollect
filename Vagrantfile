Vagrant.configure("2") do |config|
  (1..3).each do |i|
    config.vm.define "sftp#{i}" do |node|
      node.vm.box = "ubuntu/bionic64"
      node.vm.hostname = "sftp#{i}"
      node.vm.network "private_network", ip: "192.168.56.#{100 + i}"
      
      node.vm.provision "shell", path: "scripts/sftp.sh"
      node.vm.provision "shell", path: "scripts/security-audit.sh"
      node.vm.provision "shell", path: "scripts/setup-sync.sh"
    end
  end
end