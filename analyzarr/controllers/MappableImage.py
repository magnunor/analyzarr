from BaseImage import BaseImageController
from traits.api import Bool, List, Int, Float, on_trait_change
import numpy as np

class MappableImageController(BaseImageController):
    _can_map_peaks = Bool(False)
    _is_mapping_peaks = Bool(False)
    _characteristics = List(["None","Height", "Orientation", "Eccentricity"])
    _characteristic = Int(0)
    _selected_peak = Int(0)
    _peak_ids = List([])
    _vectors = List(['None','Shifts', 'Skew'])
    _vector = Int(0)
    vector_scale = Float(1.0)

    def __init__(self, parent, treasure_chest=None, data_path='/rawdata', *args, **kw):
        super(MappableImageController, self).__init__(parent, treasure_chest, data_path,
                                              *args, **kw)
        
        if self.chest is not None:
            self.numfiles = len(self.nodes)
            if self.numfiles >0:
                self.init_plot()
                print "initialized plot for data in %s" % data_path
                self._can_crop_cells = True
                self.parent.show_image_view=True
                self.update_peak_map_choices()
    
    def get_characteristic_name(self):
        return self._characteristics[self._characteristic]

    def get_vector_name(self):
        return self._vectors[self._vector]
    
    @on_trait_change('selected_index')
    def update_peak_map_choices(self):
        # do we have any entries in the peak characteristic table for this image?
        # knowing about the arrays in the cell data group is enough - if
        #  there aren't any cells from an image, there won't be any entries.
        try:
            cell_desc = self.chest.root.cell_description
        except:
            return
        if (len(self.chest.root.cell_description.getWhereList(
               'filename == "%s"' % self.get_active_name())) > 0):
            try:
                # if this table doesn't exist, we raise an exception
                peak_table = self.chest.root.cell_peaks
            except:
                return
            try:
                #TODO: need to figure out pytables attributes
                self._peak_ids = [str(idx) for idx in 
                              range(peak_table.getAttr('number_of_peaks'))]
            except:
                return
            self._can_map_peaks=True
            self.update_image()
        else:
            # clear the image and disable the comboboxes
            pass
    
    def get_characteristic_plot_title(self):
        name = ""
        if self.get_characteristic_name() != "None":
            name = ", "+self.get_characteristic_name()
            if self.get_vector_name() !="None":
                name += " and %s"%self.get_vector_name()
            name += " from peak %i" %self._selected_peak
        elif self.get_vector_name() != "None":
            name = ", "+ self.get_vector_name()
            name += " from peak %i" %self._selected_peak
        return self.get_active_name() + name
    
    @on_trait_change('_peak_ids, _characteristic, _selected_peak, _vector, \
                        selected_index, vector_scale')
    def update_image(self):
        super(MappableImageController, self).update_image()
        try:
            self.chest.getNode('/','cell_peaks')
        except:
            return
        values = \
                self.chest.root.cell_description.readWhere(
                    'filename == "%s"' % self.get_active_name(),
                    field='x_coordinate',) \
                + \
                self.chest.root.cell_peaks.readWhere(
                    'filename == "%s"' % self.get_active_name(),
                    field='y%i'%self._selected_peak,)
        
        indices = \
                self.chest.root.cell_description.readWhere(
                    'filename == "%s"' % self.get_active_name(),
                    field='y_coordinate',) \
                + \
                self.chest.root.cell_peaks.readWhere(
                    'filename == "%s"' % self.get_active_name(),
                    field='x%i'%self._selected_peak,)
        self.plotdata.set_data('value', values)
        self.plotdata.set_data('index', indices)
        
        if self.get_vector_name() != "None":
            field = ''
            if self.get_vector_name() == 'Shifts':
                field = 'd'
            elif self.get_vector_name() == 'Skew':
                field = 's'
            if field != '':
                x_comp = self.chest.root.cell_peaks.readWhere(
                                    'filename == "%s"' % self.get_active_name(),
                                    field='%sx%i' % (field,self._selected_peak),
                                    ).reshape((-1,1))
                y_comp = self.chest.root.cell_peaks.readWhere(
                                     'filename == "%s"' % self.get_active_name(),
                                     field='%sy%i' % (field, self._selected_peak),
                                     ).reshape((-1,1))
                vectors = np.hstack((x_comp,y_comp))
                vectors *= self.vector_scale
                self.plotdata.set_data('vectors',vectors)
            else:
                print "%s field not recognized for vector plots."%field
                if 'vectors' in self.plotdata.arrays:
                    self.plotdata.del_data('vectors')
                
        else:
            if 'vectors' in self.plotdata.arrays:
                self.plotdata.del_data('vectors')
                # clear vector data
        if self.get_characteristic_name() != "None":
            prefix = self._characteristics[self._characteristic][0].lower()
            column = prefix + str(self._selected_peak)
            self.plotdata.set_data('color', 
                               self.chest.root.cell_peaks.readWhere(
                                   'filename == "%s"' % self.get_active_name(),
                                   field=column,
                                       ),
                                   )
        else:
            if 'color' in self.plotdata.arrays:
                self.plotdata.del_data('color')

        #TODO: might want to implement the selection tool here.
        self.plot = self.get_scatter_quiver_plot(self.plotdata,
                                                      tool=None)
        self.set_plot_title(self.get_characteristic_plot_title())
        self._is_mapping_peaks=True