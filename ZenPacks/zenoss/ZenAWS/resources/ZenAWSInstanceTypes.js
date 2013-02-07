/*****************************************************************************
 * 
 * Copyright (C) Zenoss, Inc. 2011, all rights reserved.
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

// EC2InstanceTypePanel: a ComponentGridPanel customization for ZenAWS EC2 Instance
// types.
ZC.EC2InstanceTypePanel = Ext.extend(ZC.ComponentGridPanel, {
    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            componentType: 'EC2InstanceType',
            autoExpandColumn: 'name',
            fields: [
                {name: 'uid'},
                {name: 'name'}
            ],
            columns: [{
                id: 'name',
                dataIndex: 'name',
                header: _t('Instance Type'),
                width: 80,
                sortable: true
            }]
        });
        ZC.EC2InstanceTypePanel.superclass.constructor.call(this, config);
    }
});

Ext.reg('EC2InstanceTypePanel', ZC.EC2InstanceTypePanel);
ZC.registerName('EC2InstanceType', _t('Instance Type'), _t('Instance Types'));

}());
