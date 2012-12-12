/*****************************************************************************
 * 
 * Copyright (C) Zenoss, Inc. 2010, all rights reserved.
 * 
 * This content is made available according to terms specified in
 * License.zenoss under the directory where your Zenoss product is installed.
 * 
 ****************************************************************************/


(function() {
/*
* Custom component panels for UCS specific device components.
*/
var ZC = Ext.ns('Zenoss.component');

function render_link(ob) {
    if (ob && ob.uid) {
        return Zenoss.render.link(ob.uid);
    } else {
        return ob;
    }
}

// EC2InstancePanel: a ComponentGridPanel customization for ZenAWS EC2 Instance
// components.
ZC.EC2InstancePanel = Ext.extend(ZC.ComponentGridPanel, {
    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            componentType: 'EC2Instance',
            autoExpandColumn: 'state',
            fields: [
                {name: 'uid'},
                {name: 'instance_id'},
                {name: 'aws_name'},
                {name: 'placement'},
                {name: 'instance_type'},
                {name: 'image_id'},
                {name: 'state'}
            ],
            columns: [{
                id: 'instance_id',
                dataIndex: 'instance_id',
                header: _t('Instance ID'),
                width: 80,
                sortable: true
            },{
                id: 'aws_name',
                dataIndex: 'aws_name',
                header: _t('Name'),
                width: 280,
                sortable: true
            },{
                id: 'placement',
                dataIndex: 'placement',
                header: _t('Placement'),
                width: 80,
                sortable: true
            },{
                id: 'instance_type',
                dataIndex: 'instance_type',
                header: _t('Instance Type'),
                width: 80,
                sortable: true
            },{
                id: 'image_id',
                dataIndex: 'image_id',
                header: _t('AMI ID'),
                width: 80,
                sortable: true
            },{
                id: 'state',
                dataIndex: 'state',
                header: _t('State'),
                width: 80,
                sortable: true
            }]
        });
        ZC.EC2InstancePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2InstancePanel', ZC.EC2InstancePanel);
ZC.registerName('EC2Instance', _t('Instance'), _t('Instances'));

}());
