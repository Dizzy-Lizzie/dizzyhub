from __future__ import annotations

from ..models.garment import (
    GarmentPattern,
    GarmentTemplate,
    GarmentColor,
    GarmentSize,
    GarmentSizeRangeTemplate,
)

class GarmentFactory():

    def __init__(self, env):
        self.env = env


    def create_minimal_size_range_template(self,
        name='Test Size Range',
    ) -> GarmentSizeRangeTemplate:
        return self.env['garment.size.range.template'].create({
            'name': name,
        })

    def create_minimal_size(self,
        name='Large',
        code='L',
        range_tmpl_id:int=None
    ) -> GarmentSize:
        if range_tmpl_id is None:
            range_tmpl_id = self.create_minimal_size_range_template().id
        return self.env['garment.size'].create({
            'name': name,
            'code': code,
            'range_tmpl_id': range_tmpl_id
        })


    def create_minimal_pattern(self, 
        name='Test Pattern',
        code='123TEST'
    ) -> GarmentPattern:
        return self.env['garment.pattern'].create({
            'name': name,
            'code': code
        })


    def create_minimal_garment(self,
        name='Test Garment',
        pattern=None
    ) -> GarmentTemplate:
        return self.env['garment.template'].create({
            'name': name,
            'pattern_id': self.create_minimal_pattern().id
        })


    def create_minimal_color(self, 
        name='Test Color',
        code='123Test'
    )-> GarmentColor:
        return self.env['garment.color'].create({
            'name': name,
            'code': code,
        })


    def create_garment_with_optional_related(self, 
        *args,  
        name='Test Garment'
    )-> GarmentTemplate:
        vals = {}
        for arg in args:
            if type(arg) is type(self.env['garment.pattern']):
                if arg.id:
                    vals['pattern_id'] = arg.id
                else:
                    vals['pattern_id'] = self.create_minimal_pattern().id
            elif type(arg) is type(self.env['garment.color']):
                if arg.id:
                    vals['color_id'] = arg.id
                else:
                    vals['color_id'] = self.create_minimal_color().id
        if not vals.get('pattern_id'):
            vals['pattern_id'] = self.create_minimal_pattern().id

        return self.env['garment.template'].create({
            **vals,
            'name': name,
        })
