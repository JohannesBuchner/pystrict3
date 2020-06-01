import win32com, win32com.client
import pythoncom

def add_group_member( groupLoc, group, userLoc, user ):
   try:
      ad_obj=win32com.client.GetObject( "LDAP://cn=%s,%s" % (group, groupLoc) )
      ad_obj.Add( "LDAP://cn=%s,%s" % (user, userLoc)  )
      ad_obj.SetInfo()
   except pythoncom.com_error as xxx_todo_changeme:
      ( hr,msg,exc,arg ) = xxx_todo_changeme.args
      print("Error adding user %s to group %s..." % (user, group))
      print(hr, msg, exc, arg)

groupLoc = "ou=Friends,dc=Winslow,dc=residence"
userLoc = "cn=Users,dc=Winslow,dc=residence"
add_group_member( groupLoc, "Neighbours", userLoc, "Steve Urkel" )
