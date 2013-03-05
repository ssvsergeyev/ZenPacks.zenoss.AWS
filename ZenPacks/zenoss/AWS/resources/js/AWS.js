/*****************************************************************************
 *
 * Copyright (C) Zenoss, Inc. 2013, all rights reserved.
 *
 * This content is made available according to terms specified in
 * License.zenoss under the directory where your Zenoss product is installed.
 *
 ****************************************************************************/

(function(){

var ZC = Ext.ns('Zenoss.component');

ZC.registerName('EC2Account', _t('EC2 Account', _t('EC2 Accounts')));
ZC.registerName('EC2Instance', _t('Instance'), _t('Instances'));
ZC.registerName('EC2Region', _t('Region'), _t('Regions'));
ZC.registerName('EC2Volume', _t('Volume'), _t('Volumes'));
ZC.registerName('EC2VPC', _t('VPC'), _t('VPCs'));
ZC.registerName('EC2VPCSubnet', _t('VPC Subnet'), _t('VPC Subnets'));
ZC.registerName('EC2Zone', _t('Zone'), _t('Zones'));


var add_ec2account = new Zenoss.Action({
    text: _t('Add EC2 Account') + '...',
    id: 'add_ec2account-item',
    permission: 'Manage DMD',
    handler: function(btn, e){
        var win = new Zenoss.dialog.CloseDialog({
            width: 400,
            title: _t('Add EC2 Account'),
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
                    id: 'add_ec2account-accountname',
                    width: 260,
                    allowBlank: false
                }, {
                    xtype: 'textfield',
                    name: 'accesskey',
                    fieldLabel: _t('Access Key'),
                    id: 'add_ec2account-accesskey',
                    width: 260,
                    allowBlank: true
                }, {
                    xtype: 'password',
                    name: 'secretkey',
                    fieldLabel: _t('Secret Key'),
                    id: 'add_ec2account-secretkey',
                    width: 260,
                    allowBlank: true
                }, {
                    xtype: 'combo',
                    width: 260,
                    name: 'collector',
                    fieldLabel: _t('Collector'),
                    id: 'add_ec2account-collector',
                    mode: 'local',
                    store: new Ext.data.ArrayStore({
                        data: Zenoss.env.COLLECTORS,
                        fields: ['name']
                    }),
                    valueField: 'name',
                    displayField: 'name',
                    forceSelection: true,
                    editable: false,
                    allowBlank: false,
                    triggerAction: 'all',
                    selectOnFocus: false,
                    listeners: {
                        'afterrender': function(component) {
                            var index = component.store.find('name', 'localhost');
                            if (index >= 0) {
                                component.setValue('localhost');
                            }
                        }
                    }
                }],
                buttons: [{
                    xtype: 'DialogButton',
                    id: 'add_ec2account-submit',
                    text: _t('Add'),
                    formBind: true,
                    handler: function(b) {
                        var form = b.ownerCt.ownerCt.getForm();
                        var opts = form.getFieldValues();
                        
                        Zenoss.remote.AWSRouter.add_ec2account(
                            opts,
                            function(response) {
                                if(response.success){
                                    new Zenoss.dialog.SimpleMessageDialog({
                                        message: _t('Add EC2 account job submitted'),
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
                                        }).show();
                                    }
                                }
                            );
                        }
                    }, Zenoss.dialog.CANCEL]
                }]
            });
        win.show();
    }
});


var ZE = Ext.ns('Zenoss.extensions');

ZE.adddevice = ZE.adddevice instanceof Array ? ZE.adddevice : [];
ZE.adddevice.push(add_ec2account);

}());
