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

ZC.EC2ComponentGridPanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    aws_jumpToEntity: function(uid, meta_type) {
        var tree = Ext.getCmp('deviceDetailNav').treepanel;
        var tree_selection_model = tree.getSelectionModel();
        var components_node = tree.getRootNode().findChildBy(
            function(n) {
                if (n.data) {
                    return n.data.text == 'Components';
                }
                
                return n.text == 'Components';
            });
        
        var component_card = Ext.getCmp('component_card');
        
        if (components_node.data) {
            component_card.setContext(components_node.data.id, meta_type);
        } else {
            component_card.setContext(components_node.id, meta_type);
        }

        component_card.selectByToken(uid);
        var component_type_node = components_node.findChildBy(
            function(n) {
                if (n.data) {
                    return n.data.id == meta_type;
                }
                
                return n.id == meta_type;
            });
        
        if (component_type_node.select) {
            tree_selection_model.suspendEvents();
            component_type_node.select();
            tree_selection_model.resumeEvents();
        } else {
            tree_selection_model.select([component_type_node], false, true);
        }
    }
});


ZC.EC2InstancePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Instance',
            fields: [
                {name: 'uid'},
                {name: 'meta_type'},
                {name: 'name'},
                {name: 'title'},
                {name: 'region'},
                {name: 'instance_type'},
                {name: 'platform'},
                {name: 'private_ip_address'},
                {name: 'launch_time'},
                {name: 'state'},
                {name: 'severity'},
                {name: 'monitor'},
                {name: 'monitored'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 90
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                width: 110
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                sortable: true,
                width: 110
            },{
                id: 'instance_type',
                dataIndex: 'instance_type',
                header: _t('Instance Type'),
                sortable: true,
                width: 110
            },{
                id: 'platform',
                dataIndex: 'platform',
                header: _t('Platform'),
                sortable: true,
                width: 110
            },{
                id: 'private_ip_address',
                dataIndex: 'private_ip_address',
                header: _t('Private IP'),
                sortable: true,
                width: 110
            },{
                id: 'launch_time',
                dataIndex: 'launch_time',
                header: _t('Launch Time'),
                sortable: true,
                width: 180
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                sortable: true,
                width: 65
            }]
        });
        ZC.EC2InstancePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2InstancePanel', ZC.EC2InstancePanel);


ZC.EC2VPCPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2VPC',
            fields: [
                {name: 'uid'},
                {name: 'meta_type'},
                {name: 'name'},
                {name: 'title'},
                {name: 'region'},
                {name: 'cidr_block'},
                {name: 'state'},
                {name: 'collector'},
                {name: 'severity'},
                {name: 'monitor'},
                {name: 'monitored'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 90
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                width: 110
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                sortable: true,
                width: 110
            },{
                id: 'cidr_block',
                dataIndex: 'cidr_block',
                header: _t('CIDR Block'),
                sortable: true,
                width: 110
            },{
                id: 'collector',
                dataIndex: 'collector',
                header: _t('Collector'),
                sortable: true,
                width: 110
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                sortable: true,
                width: 65
            }]
        });
        ZC.EC2VPCPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2VPCPanel', ZC.EC2VPCPanel);


ZC.EC2ZonePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Zone',
            fields: [
                {name: 'uid'},
                {name: 'meta_type'},
                {name: 'name'},
                {name: 'title'},
                {name: 'region'},
                {name: 'state'},
                {name: 'severity'},
                {name: 'monitor'},
                {name: 'monitored'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 90
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                width: 110
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                sortable: true,
                width: 110
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                sortable: true,
                width: 65
            }]
        });
        ZC.EC2ZonePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2ZonePanel', ZC.EC2ZonePanel);


ZC.EC2VolumePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Volume',
            fields: [
                {name: 'uid'},
                {name: 'meta_type'},
                {name: 'name'},
                {name: 'title'},
                {name: 'region'},
                {name: 'state'},
                {name: 'create_time'},
                {name: 'size'},
                {name: 'zone'},
                {name: 'status'},
                {name: 'instance_id'},
                {name: 'devicepath'},
                {name: 'severity'},
                {name: 'monitor'},
                {name: 'monitored'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 90
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                width: 110
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                sortable: true,
                width: 110
            },{
                id: 'zone',
                dataIndex: 'zone',
                header: _t('Zone'),
                sortable: true,
                width: 110
            },{
                id: 'create_time',
                dataIndex: 'create_time',
                header: _t('Create Time'),
                sortable: true,
                width: 110
            },{
                id: 'size',
                dataIndex: 'size',
                header: _t('Size'),
                sortable: true,
                width: 110
            },{
                id: 'status',
                dataIndex: 'status',
                header: _t('Status'),
                sortable: true,
                width: 110
            },{
                id: 'instance_id',
                dataIndex: 'instance_id',
                header: _t('Instance ID'),
                sortable: true,
                width: 110
            },{
                id: 'devicepath',
                dataIndex: 'devicepath',
                header: _t('Device'),
                sortable: true,
                width: 110
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                sortable: true,
                width: 65
            }]
        });
        ZC.EC2VolumePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2VolumePanel', ZC.EC2VolumePanel);


/* Overview Panel Override */
Ext.onReady(function(){
    var REMOTE = Zenoss.remote.AWSRouter;

    function editDevicePathInfo(values, uid, className) {
        function name(uid) {
            if (!uid) {
                return 'Unknown';
            }

            if (!Ext.isString(uid)) {
                uid = uid.uid;
            }

            return uid.split('/').reverse()[0];
        }

        var FIELDWIDTH = 300;
        var deviceClassCombo = {
            xtype: 'combo',
            ref: '../deviceClass',
            minListWidth: 250,
            width: 300,
            name: 'deviceClass',
            fieldLabel: _t('Device Class'),
            id: 'setEC2Device_class',
            typeAhead: true,
            forceSelection: true,
            valueField: 'name',
            displayField: 'name',
            allowBlank: false,
            listConfig: {
                resizable: true
            },
            store: new Ext.data.DirectStore({
                id: 'deviceClassStore',
                root: 'deviceClasses',
                totalProperty: 'totalCount',
                model: 'Zenoss.model.Name',
                directFn: Zenoss.remote.DeviceRouter.getDeviceClasses
            })
        };

        var win = new Zenoss.FormDialog({
            autoHeight: true,
            width: FIELDWIDTH + 90,
            title: _t('Edit Device Class Location'),
            items: deviceClassCombo,
            buttons: [{
                text: _t('Save'),
                ref: '../savebtn',
                xtype: 'DialogButton',
                id: 'win-save-button',
                disabled: Zenoss.Security.doesNotHavePermission('Manage Device'),
                handler: function(btn){
                    var vals = btn.refOwner.deviceClass.getValue();
                    if (vals){
                        Ext.getCmp(className).setValue(vals);
                        win.destroy();
                    }
                }
            },{
                text: _t('Cancel'),
                xtype: 'DialogButton',
                id: 'win-cancel-button',
                handler: function(btn){
                    win.destroy();
                }
            }]
        });
        win.show();
        win.doLayout();
    }

    var DEVICE_SUMMARY_PANEL = 'deviceoverviewpanel_summary';
    var DEVICE_ID_PANEL = 'deviceoverviewpanel_idsummary';
    var DEVICE_DESCRIPTION_PANEL = 'deviceoverviewpanel_descriptionsummary';
    var DEVICE_CUSTOM_PANEL = 'deviceoverviewpanel_customsummary';
    var DEVICE_SNMP_PANEL = 'deviceoverviewpanel_snmpsummary';
    
    /* Summary Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_SUMMARY_PANEL, function(){
        var summarypanel = Ext.getCmp(DEVICE_SUMMARY_PANEL);
        summarypanel.hide();
        });

    /* ID Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_ID_PANEL, function(){
        var idpanel = Ext.getCmp(DEVICE_ID_PANEL);
        
        idpanel.removeField('serialNumber');
        idpanel.removeField('tagNumber');

        idpanel.addField({
            name: 'ec2accesskey',
            fieldLabel: _t('EC2 Access Key'),
            xtype: 'textfield'
            });

        idpanel.addField({
            name: 'ec2secretkey',
            fieldLabel: _t('EC2 Secret Key'),
            xtype: 'password'
            });

        });

    /* Description Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_DESCRIPTION_PANEL, function(){
        var descriptionpanel = Ext.getCmp(DEVICE_DESCRIPTION_PANEL);

        descriptionpanel.defaultType = 'devformpanel';
        
        descriptionpanel.removeField('rackSlot');
        descriptionpanel.removeField('hwManufacturer');
        descriptionpanel.removeField('hwModel');
        descriptionpanel.removeField('osManufacturer');
        descriptionpanel.removeField('osModel');

        descriptionpanel.addField({
            xtype: 'clicktoeditnolink',
            permission: 'Manage Device',
            listeners: {
                labelclick: function(p){
                    editDevicePathInfo(this.getValues(),
                                        this.contextUid,
                                        'linuxDeviceClass');
                },
                scope: this
            },
            name: 'linuxDeviceClass-edit',
            id: 'linuxDeviceClass-edit',
            fieldLabel: _t('Linux Device Class')
            });

        descriptionpanel.addField({
            xtype: 'textfield',
            name: 'linuxDeviceClass',
            id: 'linuxDeviceClass'
        });

        descriptionpanel.addField({
            xtype: 'clicktoeditnolink',
            permission: 'Manage Device',
            listeners: {
                labelclick: function(p){
                    editDevicePathInfo(this.getValues(),
                                            this.contextUid,
                                            'windowsDeviceClass');
                },

                scope: this
            },
            name: 'windowsDeviceClass-edit',
            id: 'windowsDeviceClass-edit',
            fieldLabel: _t('Windows Device Class')
            });

        descriptionpanel.addField({
            xtype: 'textfield',
            name: 'windowsDeviceClass',
            id: 'windowsDeviceClass'
        });
    });

    /* SNMP Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_SNMP_PANEL, function(){
        var snmppanel = Ext.getCmp(DEVICE_SNMP_PANEL);
        snmppanel.hide();
        });

});

})();
