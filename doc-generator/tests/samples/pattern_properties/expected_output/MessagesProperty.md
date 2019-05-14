| **Messages** { | object<br><br>* required* | The pattern property indicates that a free-form string is the unique identifier for the message within the registry. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**(pattern)** { | object | Property names follow regular expression pattern "\[A\-Za\-z0\-9\]\+" |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ClearingLogic** { | object<br><br>*<br>(null)* | The clearing logic associated with this message.  The properties within indicate that what messages are cleared by this message as well as under what conditions. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ClearsAll** | boolean<br><br>*read-only<br>(null)* | This property indicates that all prior conditions and messages are cleared provided the ClearsIf condition is met. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ClearsIf** | string<br>(enum)<br><br>*read-only<br>(null)* | This property contains the available OEM specific actions for this resource. *See ClearsIf in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ClearsMessage** [ ] | array (string, null)<br><br>*read-only* | This property contains the array of Message Ids that are cleared by this message, provided the other conditions are met. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} |   |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Description** | string<br><br>*read-only required* | This is a short description of how and when this message is to be used. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Message** | string<br><br>*read-only required* | The actual message. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**NumberOfArgs** | integer<br><br>*read-only required* | The number of arguments to be expected to be passed in as MessageArgs for this message. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Oem** {} | object | Oem extension object. See the *Resource* schema for details on this property. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ParamTypes** [ ] | array (string<br>(enum))<br><br>*read-only* | The MessageArg types, in order, for the message. *See ParamTypes in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Resolution** | string<br><br>*read-only required* | Used to provide suggestions on how to resolve the situation that caused the error. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Severity** | string<br><br>*read-only required* | This is the severity of the message. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} |   |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**(pattern)** {} [ ] | array, boolean, integer, number, object, string<br><br>*<br>(null)* | Property names follow regular expression pattern "^\(\[a\-zA\-Z\_\]\[a\-zA\-Z0\-9\_\]\*\)?@\(odata\|Redfish\|Message\)\\\.\[a\-zA\-Z\_\]\[a\-zA\-Z0\-9\_\.\]\+$" |
| } |   |   |
