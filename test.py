# print(strftime("%Y-%m-%d.%H-%M-%S", localtime()))
# print(round(-0.51))
#
# msg = "Failure to label node: " + "core-worker-2017-01-26"
# message = 'say ' + msg
# os.system(message)
import docker

client = docker.from_env()
# client.containers.run("ubuntu", "echo hello world")
client.containers.run("bfirsh/reticulate-splines", detach=True)
print(client.containers.list())
