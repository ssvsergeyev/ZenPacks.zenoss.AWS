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
var ZD = Ext.ns('Zenoss.devices');

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

        var guest_suffix = '';
        if (obj.meta_type == 'EC2Instance') {
            var guest = record.data.guest_device;
            if (guest) {
                guest_suffix = ' (' +
                    '<a href="' + guest.uid + '">guest</a>)';
            }
        }

        var link = null;
        if (isLink) {
            link = '<a href="javascript:Ext.getCmp(\'component_card\').componentgrid.jumpToEntity(\''+obj.uid+'\', \''+obj.meta_type+'\');">'+obj.title+'</a>';
        } else {
            link = obj.title;
        }

        return link + guest_suffix;
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
                {name: 'image_count'},
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
                id: 'image_count',
                dataIndex: 'image_count',
                header: _t('Number of Images'),
                width: 55
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
                {name: 'guest_device'},
                {name: 'zone'},
                {name: 'image'},
                {name: 'vpc'},
                {name: 'vpc_subnet'},
                {name: 'instance_type'},
                {name: 'platform'},
                {name: 'private_ip_address'},
                {name: 'public_ip'},
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
                id: 'zone',
                dataIndex: 'zone',
                header: _t('Zone'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'image',
                dataIndex: 'image',
                header: _t('Image'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'vpc',
                dataIndex: 'vpc',
                header: _t('VPC'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 100
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
                id: 'private_ip_address',
                dataIndex: 'private_ip_address',
                header: _t('Private IP'),
                width: 85
            },{
                id: 'public_ip',
                dataIndex: 'public_ip',
                header: _t('Public IP'),
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
                width: 150
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


ZC.EC2SnapshotPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Snapshot',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'volume'},
                {name: 'size'},
                {name: 'status'},
                {name: 'progress'},
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
                id: 'volume',
                dataIndex: 'volume',
                header: _t('Volume'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            },{
                id: 'size',
                dataIndex: 'size',
                header: _t('Volume size'),
                renderer: Zenoss.render.bytesString,
                width: 75
            },{
                id: 'progress',
                dataIndex: 'progress',
                header: _t('Progress'),
                width: 55
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
        ZC.EC2SnapshotPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2SnapshotPanel', ZC.EC2SnapshotPanel);


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
                {name: 'vpc_subnet_count'},
                {name: 'instance_count'}
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
                id: 'instance_count',
                dataIndex: 'instance_count',
                header: _t('Instances'),
                width: 75
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


ZC.VPNGatewayPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'VPNGateway',
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
                {name: 'gateway_type'},
                {name: 'state'},
                //{name: 'availability_zone'}
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
                id: 'gateway_type',
                dataIndex: 'gateway_type',
                header: _t('Gateway type'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 95
            // },{
            //     id: 'availability_zone',
            //     dataIndex: 'availability_zone',
            //     header: _t('Availability zone'),
            //     width: 95
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
        ZC.VPNGatewayPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('VPNGatewayPanel', ZC.VPNGatewayPanel);


ZC.EC2ReservationPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Reservation',
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
                {name: 'instance_type'},
                {name: 'availability_zone'},
                {name: 'duration'},
                {name: 'description'},
                {name: 'instance_tenancy'},
                {name: 'offering_type'},
                {name: 'state'}
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
                id: 'instance_type',
                dataIndex: 'instance_type',
                header: _t('Instance type'),
                width: 80
            },{
                id: 'availability_zone',
                dataIndex: 'availability_zone',
                header: _t('Availability zone'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'duration',
                dataIndex: 'duration',
                header: _t('Duration'),
                width: 95
            },{
                id: 'description',
                dataIndex: 'description',
                header: _t('Description'),
                width: 95
            },{
                id: 'instance_tenancy',
                dataIndex: 'instance_tenancy',
                header: _t('Instance tenancy'),
                width: 95
            },{
                id: 'offering_type',
                dataIndex: 'offering_type',
                header: _t('Offering type'),
                width: 95
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 95
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
        ZC.EC2ReservationPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2ReservationPanel', ZC.EC2ReservationPanel);


ZC.S3BucketPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'S3Bucket',
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'locking'},
                {name: 'creation_date'}
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
                id: 'creation_date',
                dataIndex: 'creation_date',
                header: _t('Creation date'),
                width: 100
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

Ext.reg('S3BucketPanel', ZC.S3BucketPanel);


ZC.EC2ElasticIPPanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2ElasticIP',
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
                {name: 'private_ip_address'},
                {name: 'instance_id'},
                {name: 'domain'},
                {name: 'network_interface_id'},
                {name: 'network_interface_owner_id'}
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
                header: _t('Public IP'),
                renderer: Zenoss.render.aws_entityLinkFromGrid
            },{
                id: 'private_ip_address',
                dataIndex: 'private_ip_address',
                header: _t('Private IP address'),
                width: 100
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'instance_id',
                dataIndex: 'instance_id',
                header: _t('Instance ID'),
                width: 100
            },{
                id: 'domain',
                dataIndex: 'domain',
                header: _t('Domain'),
                width: 60
            },{
                id: 'network_interface_id',
                dataIndex: 'network_interface_id',
                header: _t('Network interface ID'),
                width: 110
            },{
                id: 'network_interface_owner_id',
                dataIndex: 'network_interface_owner_id',
                header: _t('Network interface owner ID'),
                width: 150
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
        ZC.EC2ElasticIPPanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2ElasticIPPanel', ZC.EC2ElasticIPPanel);


ZC.EC2ImagePanel = Ext.extend(ZC.EC2ComponentGridPanel, {
    subComponentGridPanel: false,

    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            autoExpandColumn: 'name',
            componentType: 'EC2Image',
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
                {name: 'location'},
                {name: 'state'},
                {name: 'owner_id'},
                {name: 'architecture'},
                {name: 'platform'},
                {name: 'image_type'},
                {name: 'kernel_id'},
                {name: 'ramdisk_id'},
                {name: 'description'},
                {name: 'block_device_mapping'},
                {name: 'root_device_type'},
                {name: 'root_device_name'},
                {name: 'virtualization_type'},
                {name: 'hypervisor'},
                {name: 'instance_lifecycle'},
                {name: 'instance_count'}
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
                header: _t('Status'),
                width: 80
            },{
                id: 'location',
                dataIndex: 'location',
                header: _t('Location'),
                width: 80
            },{
                id: 'region',
                dataIndex: 'region',
                header: _t('Region'),
                renderer: Zenoss.render.aws_entityLinkFromGrid,
                width: 90
            },{
                id: 'owner_id',
                dataIndex: 'owner_id',
                header: _t('Owner ID'),
                width: 100
            },{
                id: 'architecture',
                dataIndex: 'architecture',
                header: _t('Architecture'),
                width: 100
            },{
                id: 'platform',
                dataIndex: 'platform',
                header: _t('Platform'),
                width: 90
            },{
                id: 'image_type',
                dataIndex: 'image_type',
                header: _t('Image type'),
                width: 90
            },{
                id: 'kernel_id',
                dataIndex: 'kernel_id',
                header: _t('Kernel ID'),
                width: 90
            },{
                id: 'ramdisk_id',
                dataIndex: 'ramdisk_id',
                header: _t('Ramdisk ID'),
                width: 90
            },{
                id: 'description',
                dataIndex: 'description',
                header: _t('Description'),
                width: 90
            },{
                id: 'block_device_mapping',
                dataIndex: 'block_device_mapping',
                header: _t('Block device mapping'),
                width: 90
            },{
                id: 'root_device_type',
                dataIndex: 'root_device_type',
                header: _t('Root device type'),
                width: 90
            },{
                id: 'root_device_name',
                dataIndex: 'root_device_name',
                header: _t('Root device name'),
                width: 90
            },{
                id: 'virtualization_type',
                dataIndex: 'virtualization_type',
                header: _t('Virtualization type'),
                width: 90
            },{
                id: 'hypervisor',
                dataIndex: 'hypervisor',
                header: _t('Hypervisor'),
                width: 90
            },{
                id: 'instance_count',
                dataIndex: 'instance_count',
                header: _t('Number of Instances'),
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
        ZC.EC2ImagePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2ImagePanel', ZC.EC2ImagePanel);


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
    id: 'component_snapshots',
    text: _t('Snapshots'),
    xtype: 'EC2SnapshotPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            case 'EC2Volume': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2SnapshotPanel.superclass.setContext.apply(this, [uid]);
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

Zenoss.nav.appendTo('Component', [{
    id: 'component_vpn_gateways',
    text: _t('Gateways'),
    xtype: 'VPNGatewayPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.VPNGatewayPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_reservations',
    text: _t('Reservations'),
    xtype: 'EC2ReservationPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2ReservationPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_s3buckets',
    text: _t('Buckets'),
    xtype: 'S3BucketPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Account': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.S3BucketPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_elastic_ips',
    text: _t('ElasticIPs'),
    xtype: 'EC2ElasticIPPanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2ElasticIPPanel.superclass.setContext.apply(this, [uid]);
    }
}]);

Zenoss.nav.appendTo('Component', [{
    id: 'component_images',
    text: _t('Images'),
    xtype: 'EC2ImagePanel',
    subComponentGridPanel: true,
    filterNav: function(navpanel) {
        switch (navpanel.refOwner.componentType) {
            case 'EC2Region': return true;
            default: return false;
        }
    },
    setContext: function(uid) {
        ZC.EC2ImagePanel.superclass.setContext.apply(this, [uid]);
    }
}]);

/* Overview Panel Override */
Ext.onReady(function(){
    var REMOTE = Zenoss.remote.AWSRouter;

    Ext.define("Zenoss.devices.DeviceClassDataStore", {
        extend:"Zenoss.NonPaginatedStore",
        constructor: function(config) {
            config = config || {};
            var router = config.router || Zenoss.remote.DeviceRouter;
            Ext.applyIf(config, {
                root: 'deviceClasses',
                totalProperty: 'totalCount',
                model: 'Zenoss.model.Name',
                directFn: Zenoss.remote.DeviceRouter.getDeviceClasses
            });
            this.callParent([config]);
        }
    });

    Ext.define("Zenoss.devices.DeviceClassCombo", {
        extend:"Zenoss.form.SmartCombo",
        alias: ['widget.deviceclasscombo'],
        constructor: function(config) {
            var store = (config||{}).store || new ZD.DeviceClassDataStore();
            config = Ext.applyIf(config||{}, {
                displayField: 'name',
                valueField: 'name',
                store: store,
                width: 300,
                minListWidth: 250,
                editable: true,
                typeAhead: true,
                forceSelection: true,
                allowBlank: true,
                listConfig: {
                    resizable: true
                }
            });
            this.callParent([config]);
        }
    });

    function editDeviceClassInfo(vals, uid) {
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

        var linuxDeviceClass = {
            id: 'linuxcombo',
            xtype: 'deviceclasscombo',
            name: 'linux',
            fieldLabel: _t('Linux Device Class')
        };

        var windowsDeviceClass = {
            id: 'windowscombo',
            xtype: 'deviceclasscombo',
            name: 'windows',
            fieldLabel: _t('Windows Device Class')
        };

        var win = new Zenoss.FormDialog({
            autoHeight: true,
            width: FIELDWIDTH + 90,
            title: _t('Edit Device Classes for Discovered Instances'),
            items: [{
                xtype: 'container',
                layout: 'anchor',
                autoHeight: true,
                items: [linuxDeviceClass, windowsDeviceClass]
            }],
            buttons: [{
                text: _t('Save'),
                ref: '../savebtn',
                xtype: 'DialogButton',
                id: 'win-save-button',
                disabled: Zenoss.Security.doesNotHavePermission('Manage Device'),
                handler: function(btn){
                    var form = btn.refOwner.editForm.getForm(),
                        vals = form.getValues();
                    Ext.apply(vals, {uid:uid});
                    REMOTE.setDeviceClassInfo(vals, function(r) {
                        Ext.getCmp('device_overview').load();
                        win.destroy();
                    });
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

        Ext.getCmp('linuxcombo').getStore().addListener('load', function fn(){
            Ext.getCmp('linuxcombo').setValue(
                vals.linuxDeviceClass ? vals.linuxDeviceClass.name : '');
        });

        Ext.getCmp('windowscombo').getStore().addListener('load', function fn(){
            Ext.getCmp('windowscombo').setValue(
                vals.windowsDeviceClass ? vals.windowsDeviceClass.name : '');
        });
    }

    var DEVICE_SUMMARY_PANEL = 'deviceoverviewpanel_summary';
    var DEVICE_ID_PANEL = 'deviceoverviewpanel_idsummary';
    var DEVICE_DESCRIPTION_PANEL = 'deviceoverviewpanel_descriptionsummary';
    var DEVICE_CUSTOM_PANEL = 'deviceoverviewpanel_customsummary';
    var DEVICE_SNMP_PANEL = 'deviceoverviewpanel_snmpsummary';
    var DEVICE_SYSTEM_PANEL = 'deviceoverviewpanel_systemsummary';

    /* Summary Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_SUMMARY_PANEL, function(){
        var summarypanel = Ext.getCmp(DEVICE_SUMMARY_PANEL);
        summarypanel.hide();
        });

    /* System Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_SYSTEM_PANEL, function(){
        var systempanel = Ext.getCmp(DEVICE_SYSTEM_PANEL);
        systempanel.minHeight = 100;
        });

    /* ID Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_ID_PANEL, function(){
        var idpanel = Ext.getCmp(DEVICE_ID_PANEL);
        idpanel.defaultType = 'devformpanel';
        idpanel.minHeight = 300;
        
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
        descriptionpanel.minHeight = 310;
        
        descriptionpanel.removeField('rackSlot');
        descriptionpanel.removeField('hwManufacturer');
        descriptionpanel.removeField('hwModel');
        descriptionpanel.removeField('osManufacturer');
        descriptionpanel.removeField('osModel');

        descriptionpanel.addField({
            id: 'linuxDeviceClass-edit',
            xtype: 'clicktoedit',
            name: 'linuxDeviceClass',
            fieldLabel: _t('Device Class for Discovered Linux Instances'),
            permission: 'Manage Device',
            listeners: {
                labelclick: function(p){
                    overview = Ext.getCmp('device_overview');
                    editDeviceClassInfo(overview.getValues(), overview.contextUid);
                },
                scope: this
            }
        });

        descriptionpanel.addField({
            id: 'windowsDeviceClass-edit',
            xtype: 'clicktoedit',
            name: 'windowsDeviceClass',
            fieldLabel: _t('Device Class for Discovered Windows Instances'),
            permission: 'Manage Device',
            listeners: {
                labelclick: function(p){
                    overview = Ext.getCmp('device_overview');
                    editDeviceClassInfo(overview.getValues(), overview.contextUid);
                },
                scope: this
            }
        });
    });

    /* SNMP Panel Override */
    Ext.ComponentMgr.onAvailable(DEVICE_SNMP_PANEL, function(){
        var snmppanel = Ext.getCmp(DEVICE_SNMP_PANEL);
        snmppanel.hide();
    });

});

})();
