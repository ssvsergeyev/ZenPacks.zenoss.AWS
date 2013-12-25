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
ZC.registerName('EC2Snapshot', _t('Snapshot'), _t('Snapshots'));
ZC.registerName('EC2VPC', _t('VPC'), _t('VPCs'));
ZC.registerName('EC2VPCSubnet', _t('Subnet'), _t('Subnets'));
ZC.registerName('EC2Zone', _t('Zone'), _t('Zones'));
ZC.registerName('VPNGateway', _t('Gateway'), _t('Gateways'));
ZC.registerName('EC2Reservation', _t('Reservation'), _t('Reservations'))
ZC.registerName('S3Bucket', _t('Bucket'), _t('Buckets'))
ZC.registerName('EC2ElasticIP', _t('ElasticIP'), _t('ElasticIPs'))
ZC.registerName('EC2Image', _t('Image'), _t('Images'))


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

try {
/* zRegionMNT property */
Zenoss.zproperties.registerZPropertyType('multilinekeypath', {xtype: 'multilinekeypath'});

Ext.define("Zenoss.form.MultilineKeyPath", {
    alias:['widget.multilinekeypath'],
    extend: 'Ext.form.field.Base',
    mixins: {
        field: 'Ext.form.field.Field'
    },

    constructor: function(config) {
        config = Ext.applyIf(config || {}, {
            editable: true,
            allowBlank: true,
            submitValue: true,
            triggerAction: 'all',
        });
        config.fieldLabel = "PEM file to region";
        Zenoss.form.MultilineCredentials.superclass.constructor.call(this, config);
    },

    initComponent: function() {
        this.grid = this.childComponent = Ext.create('Ext.grid.Panel', {
            hideHeaders: true,
            columns: [{
                dataIndex: 'value',
                flex: 1,
                renderer: function(value) {
                    try {
                        value = JSON.parse(value);
                        return value.region_name + ":"  + value.pem_path;
                    } catch (err) {
                        return "ERROR: Invalid entered string!";
                    }
                }
            }],

            store: {
                fields: ['value'],
                data: []
            },

            height: this.height || 150,
            width: 370,
            
            tbar: [{
                itemId: 'region_name',
                xtype: "textfield",
                scope: this,
                width: 90,
                emptyText:'Region name',
            },{
                itemId: 'pem_path',
                xtype: "textfield",
                scope: this,
                width: 180,
                emptyText:'Path to PEM file',
                value: '' //to avoid undefined value
            },{
                text: 'Add',
                scope: this,
                handler: function() {
                    var region_name = this.grid.down('#region_name');
                    var pem_path = this.grid.down('#pem_path');

                    var value = {
                        'region_name': region_name.value,
                        'pem_path': pem_path.value, 
                    };

                    if (region_name.value) {
                        this.grid.getStore().add({value: JSON.stringify(value)});
                    }

                    region_name.setValue("");
                    pem_path.setValue("");

                    this.checkChange();
                }
            },{
                text: "Remove",
                itemId: 'removeButton',
                disabled: true, // initial state
                scope: this,
                handler: function() {
                    var grid = this.grid,
                        selModel = grid.getSelectionModel(),
                        store = grid.getStore();
                    store.remove(selModel.getSelection());
                    this.checkChange();
                }
            }],

            listeners: {
                scope: this,
                selectionchange: function(selModel, selection) {
                    var removeButton = this.grid.down('#removeButton');
                    removeButton.setDisabled(Ext.isEmpty(selection));
                }
            }
        });

        this.callParent(arguments);
    },

    // --- Rendering ---
    // Generates the child component markup
    getSubTplMarkup: function() {
        // generateMarkup will append to the passed empty array and return it
        var buffer = Ext.DomHelper.generateMarkup(this.childComponent.getRenderTree(), []);
        // but we want to return a single string
        return buffer.join('');
    },

    // Regular containers implements this method to call finishRender for each of their
    // child, and we need to do the same for the component to display smoothly
    finishRenderChildren: function() {
        this.callParent(arguments);
        this.childComponent.finishRender();
    },

    // --- Resizing ---
    onResize: function(w, h) {
        this.callParent(arguments);
        this.childComponent.setSize(w - this.getLabelWidth(), h);
    },

    // --- Value handling ---
    setValue: function(values) {
        var data = [];
        if (values) {
            Ext.each(values, function(value) {
                data.push({value: value});
            });
        }
        this.grid.getStore().loadData(data);
    },

    getValue: function() {
        var data = [];
        this.grid.getStore().each(function(record) {
            data.push(record.get('value'));
        });
        return data;        
    },

    getSubmitValue: function() {
        return this.getValue();
    },
});
/* workaround for zenoss 4.1.1 */
} catch (err) {}

}());
