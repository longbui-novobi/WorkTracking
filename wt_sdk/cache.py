from uuid import getnode as getmac
from getpass import getuser

identification_cpu = "%s-%s" % (getmac(), getuser())
 