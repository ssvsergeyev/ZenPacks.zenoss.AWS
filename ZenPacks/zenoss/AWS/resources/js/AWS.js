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
ZC.registerName('VPNGateway', _t('VPN Gateway'), _t('VPN Gateways'));
ZC.registerName('EC2ReservedInstance', _t('Reserved Instance'), _t('Reserved Instances'))
ZC.registerName('S3Bucket', _t('S3 Bucket'), _t('S3 Buckets'))
ZC.registerName('EC2ElasticIP', _t('Elastic IP'), _t('Elastic IPs'))
ZC.registerName('EC2Image', _t('Image'), _t('Images'))
ZC.registerName('SQSQueue', _t('SQS Queue'), _t('SQS Queues'))

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
} catch (err) {

function renderzAWSRegionPEM(value) {
    result = [];
    try {
        var v = JSON.parse(value);
        Ext.each(v, function (val) {
            result.push(value.region_name + ":"  + value.pem_path);
        })
    } catch (err) {
        result.push("ERROR: Invalid data!");
    }
    return result.join(';');
}
/* configPropertyPanel.js override */
var router = Zenoss.remote.DeviceRouter,
    ConfigPropertyGrid,
    ConfigPropertyPanel,
    zpropertyConfigs = {};

Ext.ns('Zenoss.zproperties');
Ext.apply(zpropertyConfigs, {
    'int': {
        xtype: 'numberfield',
        allowDecimals: false
    },
    'float': {
        xtype: 'numberfield'
    },
    'string': {
        xtype: 'textfield'
    },
    'lines': {
        xtype: 'textarea'
    },
    'severity': {
        xtype: 'severity'
    },
    'boolean': {
        xtype: 'checkbox'
    },
    'password': {
        xtype: 'password'
    },
    'options': {
        xtype: 'combo',
        editable: false,
        forceSelection: true,
        autoSelect: true,
        triggerAction: 'all',
        mode: 'local'
    },
    'zSnmpCommunity': {
        xtype: Zenoss.Security.doesNotHavePermission('Manage Device') ? 'password' : 'textfield'
    },
    'zEventSeverity': {
        xtype: 'severity'
    },
    'zFailSeverity': {
        xtype: 'severity'
    },
    'zWinEventlogMinSeverity': {
        xtype: 'reverseseverity'
    }
});

/**
 * Allow zenpack authors to register custom zproperty
 * editors.
 **/
Zenoss.zproperties.registerZPropertyType = function(id, config){
    zpropertyConfigs[id] = config;
};

function showEditConfigPropertyDialog(data, grid) {
    var handler, uid, config, editConfig, dialog, type;
    uid = grid.uid;
    type = data.type;
    // Try the specific property id, next the type and finall default to string
    editConfig = zpropertyConfigs[data.id] || zpropertyConfigs[type] || zpropertyConfigs['string'];

    // in case of drop down lists
    if (Ext.isArray(data.options) && data.options.length > 0 && type == 'string') {
        // make it a combo and the options is the store
        editConfig = zpropertyConfigs['options'];
        editConfig.store = data.options;
    }

    // set the default values common to all configs
    Ext.apply(editConfig, {
        fieldLabel: _t('Value'),
        value: data.value,
        ref: 'editConfig',
        checked: data.value,
        name: data.id
    });

    // lines come in as comma separated and should be saved as such
    if (type == 'lines' && Ext.isArray(editConfig.value)){
        editConfig.value = editConfig.value.join('\n');
    }

    handler = function() {
        // save the junk and reload
        var values = dialog.editForm.getForm().getFieldValues(),
            value = values[data.id];
        if (type == 'lines') {
            // send back as an array separated by a new line
            value = value.split('\n');
        }

        Zenoss.remote.DeviceRouter.setZenProperty({
            uid: grid.uid,
            zProperty: data.id,
            value: value
        }, function(response){
            if (response.success) {
                var view = grid.getView();
                view.updateLiveRows(
                    view.rowIndex, true, true);

            }
        });

    };

    // form config
    config = {
        submitHandler: handler,
        minHeight: 300,
        autoHeight: true,
        width: 500,
        title: _t('Edit Config Property'),
        listeners: {
            show: function() {
                dialog.editForm.editConfig.focus(true, 500);
            }
        },
        items: [{
                xtype: 'displayfield',
                name: 'name',
                fieldLabel: _t('Name'),
                value: data.id
            },{
                xtype: 'displayfield',
                name: 'path',
                ref: 'path',
                fieldLabel: _t('Path'),
                value: data.path
            },{
                xtype: 'displayfield',
                name: 'type',
                ref: 'type',
                fieldLabel: _t('Type'),
                value: data.type
            }, editConfig
        ],
        // explicitly do not allow enter to submit the dialog
        keys: {

        }
    };
    dialog = new Zenoss.SmartFormDialog(config);

    if (Zenoss.Security.hasPermission('Manage DMD')) {
        dialog.show();
    }
}

ConfigPropertyGrid = Ext.extend(Zenoss.FilterGridPanel, {
    constructor: function(config) {
        config = config || {};
        var view;
        if (!Ext.isDefined(config.displayFilters)
            || config.displayFilters
           ){
            view = new Zenoss.FilterGridView({
                rowHeight: 22,
                nearLimit: 100,
                loadMask: {msg: _t('Loading. Please wait...')}
            });
        }else {
            view = new Ext.ux.grid.livegrid.GridView({
                nearLimit: 100,
                rowHeight: 22,
                getState: function() {
                    return {};
                },
                applyState: function(state) {

                },
                loadMask: {msg: _t('Loading...'),
                      msgCls: 'x-mask-loading'}

            });
        }
        // register this control for when permissions change
        Zenoss.Security.onPermissionsChange(function() {
            this.disableButtons(Zenoss.Security.doesNotHavePermission('Manage DMD'));
        }, this);

        Ext.applyIf(config, {
            autoExpandColumn: 'value',
            stripeRows: true,
            stateId: config.id || 'config_property_grid',
            autoScroll: true,
            sm: new Zenoss.ExtraHooksSelectionModel({
                singleSelect: true
            }),
            border: false,
            tbar:[
                 {
                    xtype: 'tbtext',
                    text: _t('Configuration Properties')
                },
                '-',
                {
                xtype: 'button',
                iconCls: 'customize',
                disabled: Zenoss.Security.doesNotHavePermission('Manage DMD'),
                ref: '../customizeButton',
                handler: function(button) {
                    var grid = button.refOwner,
                        data,
                        selected = grid.getSelectionModel().getSelected();
                    if (!selected) {
                        return;
                    }
                    data = selected.data;
                    showEditConfigPropertyDialog(data, grid);
                }
                }, {
                xtype: 'button',
                iconCls: 'refresh',
                ref: '../refreshButton',
                disabled: Zenoss.Security.doesNotHavePermission('Manage DMD'),
                handler: function(button) {
                    var grid = button.refOwner;
                    var view = grid.getView();
                    view.updateLiveRows(
                        view.rowIndex, true, true);
                }
                },{
                    xtype: 'button',
                    ref: '../deleteButton',

                    text: _t('Delete Local Copy'),
                    handler: function(button) {
                        var grid = button.refOwner,
                            data,
                            selected = grid.getSelectionModel().getSelected();
                        if (!selected) {
                            return;
                        }

                        data = selected.data;
                        if (data.islocal && data.path == '/') {
                            Zenoss.message.info(_t('{0} can not be deleted from the root definition.'), data.id);
                            return;
                        }
                        if (!data.islocal){
                            Zenoss.message.info(_t('{0} is not defined locally'), data.id);
                            return;
                        }
                        Ext.Msg.show({
                        title: _t('Delete Local Property'),
                        msg: String.format(_t("Are you sure you want to delete the local copy of {0}?"), data.id),
                        buttons: Ext.Msg.OKCANCEL,
                        fn: function(btn) {
                            if (btn=="ok") {
                                if (grid.uid) {
                                    router.deleteZenProperty({
                                        uid: grid.uid,
                                        zProperty: data.id
                                    }, function(response){
                                        var view = grid.getView();
                                        view.updateLiveRows(
                                            view.rowIndex, true, true);
                                    });
                                }
                            } else {
                                Ext.Msg.hide();
                            }
                        }
                    });
                    }
                }
            ],
            store: new Ext.ux.grid.livegrid.Store({
                bufferSize: 400,
                autoLoad: true,
                defaultSort: {field: 'id', direction:'ASC'},
                sortInfo: {field: 'id', direction:'ASC'},
                proxy: new Ext.data.DirectProxy({
                    directFn: Zenoss.remote.DeviceRouter.getZenProperties
                }),
                reader: new Ext.ux.grid.livegrid.JsonReader({
                    root: 'data',
                    totalProperty: 'totalCount',
                    idProperty: 'id'
                },[
                    {name: 'id'},
                    {name: 'islocal'},
                    {name: 'value'},
                    {name: 'category'},
                    {name: 'valueAsString'},
                    {name: 'type'},
                    {name: 'path'},
                    {name: 'options'}
                ])
            }),
            cm: new Ext.grid.ColumnModel({
                columns: [{
                    header: _t("Is Local"),
                    id: 'islocal',
                    dataIndex: 'islocal',
                    width: 60,
                    sortable: true,
                    filter: false,
                    renderer: function(value){
                        if (value) {
                            return 'Yes';
                        }
                        return '';
                    }
                },{
                    id: 'category',
                    dataIndex: 'category',
                    header: _t('Category'),
                    soheader: _t("Is Local"),rtable: true
                },{
                    id: 'id',
                    dataIndex: 'id',
                    header: _t('Name'),
                    width: 200,
                    sortable: true
                },{
                    id: 'value',
                    dataIndex: 'valueAsString',
                    header: _t('Value'),
                    width: 180,
                    renderer: function(v, row, record) {
                        // renderer for zAWSRegionPEM
                        if (record.id == 'zAWSRegionPEM' &&
                            record.get('value') !== "") {
                            return renderzAWSRegionPEM(record.get('value'));
                        }
                        if (Zenoss.Security.doesNotHavePermission("Manage Device") &&
                            record.data.id == 'zSnmpCommunity') {
                            return "*******";
                        }
                        return v;
                    },
                    sortable: false
                },{
                    id: 'path',
                    dataIndex: 'path',
                    header: _t('Path'),
                    width: 200,
                    sortable: true
                }]
            }),
            view: view
        });
        ConfigPropertyGrid.superclass.constructor.apply(this, arguments);
        this.on('rowdblclick', this.onRowDblClick, this);
    },

    setContext: function(uid) {
        this.uid = uid;
        // set the uid and load the grid
        var view = this.getView();
        view.contextUid  = uid;
        this.getStore().setBaseParam('uid', uid);
        this.getStore().load();
        if (uid == '/zport/dmd/Devices'){
            this.deleteButton.setDisabled(true);
        } else {
            this.deleteButton.setDisabled(Zenoss.Security.doesNotHavePermission('Manage DMD'));
        }

    },
    onRowDblClick: function(grid, rowIndex, e) {
        var data,
            selected = grid.getSelectionModel().getSelected();
        if (!selected) {
            return;
        }
        data = selected.data;
        showEditConfigPropertyDialog(data, grid);
    },
    disableButtons: function(bool) {
        this.deleteButton.setDisabled(bool);
        this.customizeButton.setDisabled(bool);
    }
});

ConfigPropertyPanel = Ext.extend(Ext.Panel, {
    constructor: function(config) {
        config = config || {};
        Ext.applyIf(config, {
            layout: 'fit',
            autoScroll: 'y',
            height: 800,
            items: [new ConfigPropertyGrid({
                ref: 'configGrid',
                displayFilters: config.displayFilters
            })]

        });
        ConfigPropertyPanel.superclass.constructor.apply(this, arguments);
    },
    setContext: function(uid) {
        this.configGrid.setContext(uid);
    }
});

Ext.reg('configpropertypanel', ConfigPropertyPanel);

}

}());
