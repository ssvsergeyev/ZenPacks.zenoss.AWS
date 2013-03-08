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

Ext.apply(Zenoss.render, {
    aws_entityLinkFromGrid: function(obj, col, record) {
        if (!obj)
            return;

        if (typeof(obj) == 'string')
            obj = record.data;

        if (!obj.title && obj.name)
            obj.title = obj.name;

        var isLink = false;

        if (this.refName == 'componentgrid') {
            // Zenoss >= 4.2 / ExtJS4
            if (this.subComponentGridPanel || this.componentType != obj.meta_type)
                isLink = true;
        } else {
            // Zenoss < 4.2 / ExtJS3
            if (!this.panel || this.panel.subComponentGridPanel)
                isLink = true;
        }

        if (isLink) {
            return '<a href="javascript:Ext.getCmp(\'component_card\').componentgrid.jumpToEntity(\''+obj.uid+'\', \''+obj.meta_type+'\');">'+obj.title+'</a>';
        } else {
            return obj.title;
        }
    }
});

ZC.EC2ComponentGridPanel = Ext.extend(ZC.ComponentGridPanel, {
    subComponentGridPanel: false,

    jumpToEntity: function(uid, meta_type) {
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


ZC.EC2RegionPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Region',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'zone_count'},
                {name: 'instance_count'},
                {name: 'volume_count'},
                {name: 'vpc_count'},
                {name: 'vpc_subnet_count'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'zone_count',
                dataIndex: 'zone_count',
                header: _t('Zones'),
                width: 55
            },{
                id: 'instance_count',
                dataIndex: 'instance_count',
                header: _t('Instances'),
                width: 75
            },{
                id: 'volume_count',
                dataIndex: 'volume_count',
                header: _t('Volumes'),
                width: 65
            },{
                id: 'vpc_count',
                dataIndex: 'vpc_count',
                header: _t('VPCs'),
                width: 55
            },{
                id: 'vpc_subnet_count',
                dataIndex: 'vpc_subnet_count',
                header: _t('Subnets'),
                width: 90
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2RegionPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2RegionPanel', ZC.EC2RegionPanel);


ZC.EC2ZonePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Zone',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'region'},
                {name: 'state'},
                {name: 'instance_count'},
                {name: 'volume_count'},
                {name: 'vpc_subnet_count'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'instance_count',
                dataIndex: 'instance_count',
                header: _t('Instances'),
                width: 75
            },{
                id: 'volume_count',
                dataIndex: 'volume_count',
                header: _t('Volumes'),
                width: 65
            },{
                id: 'vpc_subnet_count',
                dataIndex: 'vpc_subnet_count',
                header: _t('Subnets'),
                width: 90
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2ZonePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2ZonePanel', ZC.EC2ZonePanel);


ZC.EC2InstancePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Instance',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'region'},
                {name: 'zone'},
                {name: 'vpc_subnet'},
                {name: 'instance_type'},
                {name: 'platform'},
                {name: 'public_ip_address'},
                {name: 'private_ip_address'},
                {name: 'volume_count'},
                {name: 'state'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'zone',
                dataIndex: 'zone',
                header: _t('Zone'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'vpc_subnet',
                dataIndex: 'vpc_subnet',
                header: _t('Subnet'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 100
            },{
                id: 'instance_type',
                dataIndex: 'instance_type',
                header: _t('Type'),
                width: 70
            },{
                id: 'platform',
                dataIndex: 'platform',
                header: _t('Platform'),
                width: 65
            },{
                id: 'public_ip_address',
                dataIndex: 'public_ip_address',
                header: _t('Public IP'),
                width: 85
            },{
                id: 'private_ip_address',
                dataIndex: 'private_ip_address',
                header: _t('Private IP'),
                width: 85
            },{
                id: 'volume_count',
                dataIndex: 'volume_count',
                header: _t('Volumes'),
                width: 65
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2InstancePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2InstancePanel', ZC.EC2InstancePanel);


ZC.EC2VolumePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Volume',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'region'},
                {name: 'zone'},
                {name: 'instance'},
                {name: 'size'},
                {name: 'iops'},
                {name: 'status'},
                {name: 'attach_data_status'},
                {name: 'attach_data_devicepath'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'status',
                dataIndex: 'status',
                header: _t('Status'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'zone',
                dataIndex: 'zone',
                header: _t('Zone'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'instance',
                dataIndex: 'instance',
                header: _t('Instance'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 80
            },{
                id: 'size',
                dataIndex: 'size',
                header: _t('Size'),
                renderer: Zenoss.render.bytesString,
                width: 55
            },{
                id: 'iops',
                dataIndex: 'iops',
                header: _t('IOPS'),
                width: 55
            },{
                id: 'attach_data_status',
                dataIndex: 'attach_data_status',
                header: _t('Attach Status'),
                width: 90
            },{
                id: 'attach_data_devicepath',
                dataIndex: 'attach_data_devicepath',
                header: _t('Attach Device'),
                width: 85
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2VolumePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2VolumePanel', ZC.EC2VolumePanel);


ZC.EC2VPCPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2VPC',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'region'},
                {name: 'state'},
                {name: 'cidr_block'},
                {name: 'collector'},
                {name: 'vpc_subnet_count'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'cidr_block',
                dataIndex: 'cidr_block',
                header: _t('CIDR Block'),
                width: 95
            },{
                id: 'collector',
                dataIndex: 'collector',
                header: _t('Collector'),
                width: 110
            },{
                id: 'vpc_subnet_count',
                dataIndex: 'vpc_subnet_count',
                header: _t('Subnets'),
                width: 90
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2VPCPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2VPCPanel', ZC.EC2VPCPanel);


ZC.EC2VPCSubnetPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2VPCSubnet',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'state'},
                {name: 'region'},
                {name: 'zone'},
                {name: 'vpc'},
                {name: 'cidr_block'},
                {name: 'instance_count'},
                {name: 'available_ip_address_count'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 50
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Name'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'zone',
                dataIndex: 'zone',
                header: _t('Zone'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'vpc',
                dataIndex: 'vpc',
                header: _t('VPC'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 110
            },{
                id: 'cidr_block',
                dataIndex: 'cidr_block',
                header: _t('CIDR Block'),
                width: 95
            },{
                id: 'instance_count',
                dataIndex: 'instance_count',
                header: _t('Instances'),
                width: 75
            },{
                id: 'available_ip_address_count',
                dataIndex: 'available_ip_address_count',
                header: _t('Available IPs'),
                width: 85
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });
        ZC.EC2VPCSubnetPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2VPCSubnetPanel', ZC.EC2VPCSubnetPanel);


/* Subcomponent Panels */

Zenoss.nav.appendTo('Component', [{
    id: 'component_instances',
    text: _t('Instances'),
    xtype: 'EC2InstancePanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            case 'EC2Zone': return true;
            case 'EC2VPC': return true;
            case 'EC2VPCSubnet': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2InstancePanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_volumes',
    text: _t('Volumes'),
    xtype: 'EC2VolumePanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            case 'EC2Zone': return true;
            case 'EC2Instance': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2VolumePanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_vpcs',
    text: _t('VPCs'),
    xtype: 'EC2VPCPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            case 'EC2Zone': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2VPCPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_vpc_subnets',
    text: _t('Subnets'),
    xtype: 'EC2VPCSubnetPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            case 'EC2Zone': return true;
            case 'EC2VPC': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2VPCSubnetPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_zones',
    text: _t('Zones'),
    xtype: 'EC2ZonePanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2ZonePanel.superclass.setContext.apply(this, [uid]);
    }
}]);


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
