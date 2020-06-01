import winreg
x=winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
y= winreg.OpenKey(x,
 r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
print("Your environment variables are")
print("#","name","value","type")
for i in range(1000):
    try:
        n,v,t=winreg.EnumValue(y,i)
        print(i,n,v,t)
    except EnvironmentError:
        print("You have",i,"Environment variables")
        break
print("Your PATH was ")    
path = winreg.QueryValueEx(y,"path")[0]
print(path)
winreg.CloseKey(y)
# Reopen Environment key for writing.
y=winreg.OpenKey(x,
 r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
 0,winreg.KEY_ALL_ACCESS)
# now append C:\ to the path
winreg.SetValueEx(y,"path",0,winreg.REG_EXPAND_SZ,path+";C:\\")
winreg.CloseKey(y)
winreg.CloseKey(x)
