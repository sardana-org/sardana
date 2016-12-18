import PyTango
import taurus
import csv
import sys

def checkPoolElements(pool):
    pool_dev = taurus.Device(pool)

    # GET CONTROLLER CLASSES
    pool_ctrl_classes = {}
    for info in pool_dev['ControllerClassList'].value:
        ctrl_class, library_path, ctrl_type = info.split()
        pool_ctrl_classes[ctrl_class] = (library_path, ctrl_type)

    # GET CONTROLLERS INFO
    pool_controllers_by_type = {'Motor': [],
                                'PseudoMotor': [],
                                'IORegister': [],
                                'CounterTimer': [],
                                'PseudoCounter': [],
                                'ZeroDExpChannel': []}

    pool_controllers = {}
    for info in pool_dev['ControllerList'].value:
        info_splitted = info.split()
        ctrl_name = info_splitted[0]
        ctrl_library = info_splitted[-1].replace('(','').replace(')','')
        ctrl_class = info_splitted[1].rsplit('.')[1].split('/')[0]
        ctrl_type = ''
        try:
            ctrl_type = pool_ctrl_classes[ctrl_class][1]
            pool_controllers_by_type[ctrl_type].append(ctrl_name)
        except:
            pass
        ctrl_properties = {}
        ctrl_elements = []
        ctrl_pool_elements = []
        for prop in pool_dev.get_property_list(ctrl_name+'/*'):
            prop_name = prop.split('/')[1]
            prop_value = pool_dev.get_property(prop)[prop]
            ctrl_properties[prop_name] = ' '.join(prop_value)
        pool_controllers[ctrl_name] = {}
        pool_controllers[ctrl_name]['type'] = ctrl_type
        pool_controllers[ctrl_name]['pool'] = pool
        pool_controllers[ctrl_name]['name'] = ctrl_name
        pool_controllers[ctrl_name]['file'] = ctrl_library
        pool_controllers[ctrl_name]['class'] = ctrl_class
        pool_controllers[ctrl_name]['properties'] = ctrl_properties
        pool_controllers[ctrl_name]['elements'] = ctrl_elements
        pool_controllers[ctrl_name]['ctrl_pool_elements'] = ctrl_pool_elements


    pool_elements = {}
    pool_elements['ExpChannels'] = pool_dev['ExpChannelList'].value or []
    pool_elements['Motors'] = pool_dev['MotorList'].value or []
    pool_elements['IORegs'] = pool_dev['IORegisterList'].value or []
    pool_instruments = pool_dev['InstrumentList'].value or []


    pool_measurement_groups = {}
    for info in pool_dev['MeasurementGroupList'].value:
        info_splitted = info.split()
        mg_name = info_splitted[0]
        pool_measurement_groups[mg_name] = []
        for channel in info_splitted[4:]:
            if not channel.startswith('('):
                channel_name = channel.replace(',','')
                pool_measurement_groups[mg_name].append(channel_name)
            else:
                break

    ### print '\n'
    ### print '----------------------------------------------------------------'
    ### print 'ELEMENTS FOR POOL ' + pool
    ### print '----------------------------------------------------------------'
    ### for element_type in pool_elements.keys():
    ###     elements = pool_elements[element_type]
    ###     print element_type+':',len(elements)

    db = taurus.Database()
    pool_elements_detail = {}
    for element_type in pool_elements.keys():
        elements = pool_elements[element_type]
        for info in elements:
            info_splitted = info.split()
            alias = info_splitted[0]
            dev_name = info_splitted[1].replace('(','').replace(')','')
            ctrl_name, ctrl_axis = info_splitted[2].replace('(','').replace(')','').split('/')
            specific_element_type = info_splitted[3]

            element_dev = taurus.Device(alias)

            pool_elements_detail[alias] = {}
            pool_elements_detail[alias]['type'] = specific_element_type
            pool_elements_detail[alias]['pool'] = pool
            pool_elements_detail[alias]['ctrl'] = ctrl_name
            pool_elements_detail[alias]['name'] = alias
            pool_elements_detail[alias]['axis'] = dev_name.rsplit('/',1)[1]           
            pool_elements_detail[alias]['instrument'] = element_dev.Instrument.split('(')[0]
            pool_elements_detail[alias]['attr_dicts'] = {}
            
            for attr, attr_dict in db.get_device_attribute_property(element_dev.getNormalName(), element_dev.get_attribute_list()).iteritems():
                if len(attr_dict) > 0:
                    pool_elements_detail[alias]['attr_dicts'][attr] = attr_dict
                else:
                    if attr.lower() in ['position', 'value']:
                        print '***',specific_element_type, alias, attr,  'NO MEMORIZED ATTRIBUTES OR ATTRIBUTE CONFIGURATIONS ***'


    ### print '\n'
    ### print '----------------------------------------------------------------'
    ### print len(pool_instruments),'INSTRUMENTS FOR POOL ' + pool
    ### print '----------------------------------------------------------------'
    ### print pool_instruments

    # CHECK ELEMENTS WITHOUT INSTRUMENT
    for element_type in pool_elements.keys():
        elements = pool_elements[element_type]
        elements_with_no_instrument = []
        for info in elements:
            info_splitted = info.split()
            alias = info_splitted[0]
            dev_name = info_splitted[1]
            ctrl_name, ctrl_axis = info_splitted[2].replace('(','').replace(')','').split('/')
            specific_element_type = info_splitted[3]

            # Add info of 'physicals needed' in pseudomotor and pseudocounter controllers
            pool_controllers[ctrl_name]['ctrl_pool_elements'].append(alias)
            if specific_element_type in ['PseudoMotor', 'PseudoCounter']:
                ###########################################################################################
                # There is a bug in the Pool's ExpChannelList attribute that does not                     #
                # provide any physical channels for the pseudo channels, this info, is                    #
                # available in the Pool's PseudoCounterList so, while this bug is not fixed               #
                # We will have to - INEFFICIENTLY - read the PseudoCounter list again for each pseudo     #
                # pseudo counter in order to put the info                                                 #
                if len(pool_controllers[ctrl_name]['elements']) == 0:                                     #
                    if specific_element_type == 'PseudoCounter':                                          #
                        for info in pool_dev['PseudoCounterList'].value or []:                            #
                            info_splitted = info.split()                                                  #
                            alias_again = info_splitted[0]                                                #
                            if alias_again == alias:                                                      #
                                break                                                                     #
                ###########################################################################################
                    pool_controllers[ctrl_name]['elements'] = ' '.join(info_splitted[6:])


            element_dev = taurus.Device(alias)
            if element_dev['Instrument'].value == '':
                elements_with_no_instrument.append(alias)
        ### if len(elements_with_no_instrument) > 0:
        ###     print '\n***',element_type,'with no Instrument:',elements_with_no_instrument,'***'


    ### for ctrl_type, controllers in pool_controllers_by_type.iteritems():
    ###     if len(controllers) == 0:
    ###         continue
    ###     
    ###     print '\n'
    ###     print '----------------------------------------------------------------'
    ###     print len(controllers), ctrl_type, 'CONTROLLERS FOR POOL ' + pool
    ###     print '----------------------------------------------------------------'
    ### 
    ###     for ctrl in controllers:
    ###         ###print 'Controller',ctrl,':'
    ###         ###for k, v in details.iteritems():
    ###         ###    if k == 'ctrl_pool_elements':
    ###         ###        print '\tElements count:\t'+str(len(v))
    ###         ###    print '\t'+k+':\t'+str(v)
    ###         ###
    ###         ###pool_controllers[ctrl_name]['type'] = ctrl_type
    ###         ###pool_controllers[ctrl_name]['name'] = ctrl_name
    ###         ###pool_controllers[ctrl_name]['file'] = ctrl_library
    ###         ###pool_controllers[ctrl_name]['class'] = ctrl_class
    ###         ###pool_controllers[ctrl_name]['properties'] = ctrl_properties
    ###         ###pool_controllers[ctrl_name]['elements'] = ctrl_elements
    ###         ###pool_controllers[ctrl_name]['ctrl_pool_elements'] = ctrl_pool_elements
    ### 
    ###         details = pool_controllers[ctrl]
    ###         pool_elements_summary = '('+str(len(details['ctrl_pool_elements']))+')'
    ###         print '{type}\t{name}\t{file}\t{class}\t{properties}\t{elements}'.format(**details), pool_elements_summary
            



    columns = ['Type', 'Pool', 'Name', 'File', 'Class', 'Properties', 'Elements', 'MOT', 'PMOT', 'IOR', 'CT', 'PC', 'ZD']
    controllers_sheet = ''
    row = '\t'.join(columns)
    controllers_sheet += row + '\n'

    columns = ['Type', 'Pool', 'Name', 'Class']
    instruments_sheet = ''
    row = '\t'.join(columns)
    instruments_sheet += row + '\n'

    columns = ['Type', 'Pool', 'Controller', 'Name', 'DeviceName', 'Axis', 'Instrument', 'Description', 'Attributes']
    motors_sheet = ''
    row = '\t'.join(columns)
    motors_sheet += row + '\n'
    
    ioregs_sheet = ''
    row = '\t'.join(columns)
    ioregs_sheet += row + '\n'
    
    channels_sheet = ''
    row = '\t'.join(columns)
    channels_sheet += row + '\n'
    
    columns = ['Type', 'Pool', 'Name', 'DeviceName', 'Channels', 'Description']
    acquisition_sheet = ''
    row = '\t'.join(columns)
    acquisition_sheet += row + '\n'
    
    columns = ['Pool', 'Element', 'Parameter', 'Label', 'Format', 'Min Value', 'Min Alarm', 'Min Warning', 'Max Warning', 'Max Alarm', 'Max Value', 'Unit', 'Polling Period', 'Change Event', 'Description']
    parameters_sheet = ''
    row = '\t'.join(columns)
    parameters_sheet += row + '\n'
    
    for ctrl_type, controllers in pool_controllers_by_type.iteritems():
        if len(controllers) == 0:
            continue
        for ctrl in controllers:
            ctrl_details = pool_controllers[ctrl]

            for element_type in ['Motor', 'PseudoMotor', 'IORegister', 'CounterTimer', 'PseudoCounter', 'ZeroDExpChannel']:
                ctrl_details[element_type] = 0
                if ctrl_type == element_type:
                    ctrl_details[element_type] = len(ctrl_details['ctrl_pool_elements'])

            if len(ctrl_details['properties']) == 0:
                ctrl_details['properties'] = ''
            else:
                properties = []
                for k,v in ctrl_details['properties'].iteritems():
                    properties.append(k+':'+v)
                ctrl_details['properties'] = '; '.join(properties)

            if len(ctrl_details['elements']) == 0:
                ctrl_details['elements'] = ''
            else:
                ctrl_details['elements'] = ctrl_details['elements'].replace(',',';')

            ctrl_row_template = '{type}\t{pool}\t{name}\t{file}\t{class}\t{properties}\t{elements}\t{Motor}\t{PseudoMotor}\t{IORegister}\t{CounterTimer}\t{PseudoCounter}\t{ZeroDExpChannel}'
            row = ctrl_row_template.format(**ctrl_details)
            controllers_sheet += row + '\n'

            for alias in ctrl_details['ctrl_pool_elements']:
                elem_details = pool_elements_detail[alias]
                elem_type = elem_details['type']
                attr_dicts = elem_details['attr_dicts'] 
                attribute_values = []
                for attr in attr_dicts.keys():
                    attr_dict = attr_dicts[attr]
                    if attr_dict.has_key('__value'):
                        attribute_values.append(attr+':'+attr_dict['__value'][0])

                    elem_params = {}
                    ['Pool', 'Element', 'Parameter', 'Label', 'Format', 'Min Value', 'Min Alarm', 'Min Warning', 'Max Warning', 'Max Alarm', 'Max Value', 'Unit', 'Polling Period', 'Change Event', 'Description']
                    elem_params['pool'] = pool
                    elem_params['element'] = alias
                    elem_params['parameter'] = attr
                    elem_params['label'] = attr_dict.get('label',[''])[0]
                    elem_params['format'] = attr_dict.get('format',[''])[0]
                    elem_params['min_value'] = attr_dict.get('min_value',[''])[0]
                    elem_params['min_alarm'] = attr_dict.get('min_alarm',[''])[0]
                    elem_params['min_warning'] = attr_dict.get('min_warning',[''])[0]
                    elem_params['max_warning'] = attr_dict.get('max_warning',[''])[0]
                    elem_params['max_alarm'] = attr_dict.get('max_alarm',[''])[0]
                    elem_params['max_value'] = attr_dict.get('max_value',[''])[0]
                    elem_params['unit'] = attr_dict.get('unit',[''])[0]
                    elem_params['polling'] = attr_dict.get('event_period',[''])[0]
                    elem_params['event'] = attr_dict.get('abs_change',[''])[0]

                    for k,v in elem_params.iteritems():
                        if v != '' and k not in ['pool','element', 'parameter']:
                            params_row_template = '{pool}\t{element}\t{parameter}\t{label}\t{format}\t{min_value}\t{min_alarm}\t{min_warning}\t{max_warning}\t{max_alarm}\t{max_value}\t{unit}\t{polling}\t{event}'
                            row = params_row_template.format(**elem_params)
                            parameters_sheet += row + '\n'
                            break

                elem_details['attrs'] = ';'.join(attribute_values)
                elem_row_template = '{type}\t{pool}\t{ctrl}\t{name}\tAutomatic\t{axis}\t{instrument}\t\t{attrs}'
                row = elem_row_template.format(**elem_details)
                if elem_type in ['Motor', 'PseudoMotor']:
                    motors_sheet += row + '\n'
                elif elem_type == 'IORegister':
                    ioregs_sheet += row + '\n'
                else:
                    channels_sheet += row + '\n'

    instrument_row_template = '{type}\t{pool}\t{name}\t{class}'
    for instrument in pool_instruments:
        instrument_details = {}
        instrument_details['type'] = 'Instrument'
        instrument_details['pool'] = pool
        instrument_details['name'] = instrument.split('(')[0]
        instrument_details['class'] = instrument.split('(')[1].replace(')','')
        row = instrument_row_template.format(**instrument_details)
        instruments_sheet += row + '\n'

    acq_row_template = '{type}\t{pool}\t{name}\tAutomatic\t{channels}'
    for mg_name, mg_channels in pool_measurement_groups.iteritems():
        mg_details = {}
        mg_details['type'] = 'MeasurementGroup'
        mg_details['pool'] = pool
        mg_details['name'] = mg_name
        mg_details['channels'] = ';'.join(mg_channels)
        row = acq_row_template.format(**mg_details)
        acquisition_sheet += row + '\n'

    print '\n'*2
    print '################################ CONTROLLERS ################################\n'*4
    print '\n'*2
    print controllers_sheet
    print '\n'*2
    print '################################ INSTRUMENTS ################################\n'*4
    print '\n'*2
    print instruments_sheet
    print '\n'*2
    print '################################    MOTORS   ################################\n'*4
    print '\n'*2
    print motors_sheet
    print '\n'*2
    print '################################    IOREGS   ################################\n'*4
    print '\n'*2
    print ioregs_sheet
    print '\n'*2
    print '################################   CHANNELS  ################################\n'*4
    print '\n'*2
    print channels_sheet
    print '\n'*2
    print '################################ ACQUISITION ################################\n'*4
    print '\n'*2
    print acquisition_sheet
    print '\n'*2
    print '################################ PARAMETERS  ################################\n'*4
    print '\n'*2
    print parameters_sheet





if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] == '?':
        print '----------------------------------------'
        print 'Invalid number of arguments.'
        print ''
        print 'Example of usage:'
        print '    python get_pool_config pool'
        print ''
        print '    where pool is the device name of the pool'
        print '----------------------------------------'


    pool = sys.argv[1]
    checkPoolElements(pool)
