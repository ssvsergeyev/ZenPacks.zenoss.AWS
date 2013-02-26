(function(){

var add_ec2manager = new Zenoss.Action({
    text: _t('Add EC2 Manager') + '...',
    id: 'addec2manager-item',
    permission: 'Manage DMD',
    handler: function(btn, e){
        var win = new Zenoss.dialog.CloseDialog({
            width: 400,
            title: _t('Add EC2 Manager'),
            items: [{
                xtype: 'form',
                buttonAlign: 'left',
                monitorValid: true,
                labelAlign: 'top',
                footerStyle: 'padding-left: 0',
                border: false,
                items: [{
                    xtype: 'textfield',
                    name: 'accountname',
                    fieldLabel: _t('Account Name'),
                    id: 'ec2accountname',
                    width: 260,
                    allowBlank: false
                }, {
                    xtype: 'textfield',
                    name: 'accesskey',
                    fieldLabel: _t('Access Key'),
                    id: 'ec2accesskey',
                    width: 260,
                    allowBlank: true
                }, {
                    xtype: 'password',
                    name: 'secretkey',
                    fieldLabel: _t('Secret Key'),
                    id: 'ec2secretkey',
                    width: 260,
                    allowBlank: true
                }],
                buttons: [{
                    xtype: 'DialogButton',
                    id: 'addec2manager-submit',
                    text: _t('Add'),
                    formBind: true,
                    handler: function(b) {
                        var form = b.ownerCt.ownerCt.getForm();
                        var opts = form.getFieldValues();
                        
                        Zenoss.remote.EC2ManagerRouter.add_ec2manager(opts,
                            function(response) {
                                if(response.success){
                                    new Zenoss.dialog.SimpleMessageDialog({
                                        message: _t('Add EC2 Manager job submitted.'),
                                        buttons: [{
                                            xtype: 'DialogButton',
                                            text: _t('OK')
                                        }
                                        ]
                                        }).show();
                                    }
                                else {
                                    new Zenoss.dialog.SimpleMessageDialog({
                                        message: response.msg,
                                        buttons: [{
                                            xtype: 'DialogButton',
                                            text: _t('OK')
                                            }]
                                        }).show(); //close of new
                                    } // close of else
                                } // close of function
                            ); // close of zenoss.remote.SMISProverRouter
                        } //close of handler
                    }, Zenoss.dialog.CANCEL] //close of button
                }] // close of items
            }); //close of var
        win.show();
    } //close of handler
}); // close of smisprovider

// Push the addSMISProvider action to the adddevice button

var zExt = Ext.ns('Zenoss.extensions');

zExt.adddevice = zExt.adddevice instanceof Array ?
                            zExt.adddevice : [];
zExt.adddevice.push(add_ec2manager);

}());
