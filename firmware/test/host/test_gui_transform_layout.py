"""Exercise actual transform application without repeated whole-tree layout for ordinary nodes."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


def exercise(component, directory):
    source = (component / 'src/props_common.cpp').read_text()
    start = source.index('int32_t resolve_pivot_value(')
    actual = source[start:source.index('void apply_common_flags(', start)]
    area = (ROOT / 'firmware/managed_components/lvgl__lvgl/src/misc/lv_area.c').read_text()
    pivot_start = area.index('int32_t lv_pct(')
    pivot_helpers = area[pivot_start:area.index('/**********************', pivot_start)]
    code = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#define LV_CONF_SKIP 1
#include "lvgl.h"
struct Object{int width=200,height=100,pivot_x=0,pivot_y=0,zoom=256,angle=0;};
struct Record{Object* object;};
struct PivotValue{bool percent=false;int value=0;};
struct CommonProps{PivotValue pivot_x,pivot_y;int zoom=256,angle=0;};
int layouts=0;
void lv_obj_update_layout(Object*){++layouts;}
int lv_obj_get_width(Object* object){return object->width;}
int lv_obj_get_height(Object* object){return object->height;}
void lv_obj_set_style_transform_pivot_x(Object* object,int value,int){object->pivot_x=value;}
void lv_obj_set_style_transform_pivot_y(Object* object,int value,int){object->pivot_y=value;}
void lv_obj_set_style_transform_scale(Object* object,int value,int){object->zoom=value;}
void lv_obj_set_style_transform_rotation(Object* object,int value,int){object->angle=value;}
''' + pivot_helpers + actual + r'''
int main(){
 Object object;Record record{&object};CommonProps props;
 for(int node=0;node<3000;++node)apply_common_transform(record,props);
 assert(layouts==0 && object.zoom==256 && object.angle==0);
 props.zoom=128;props.angle=45;props.pivot_x={true,50};props.pivot_y={true,50};apply_common_transform(record,props);
 assert(layouts==0 && object.pivot_x==lv_pct(50) && object.pivot_y==lv_pct(50) && object.zoom==128 && object.angle==450);
 props.pivot_x={false,17};props.pivot_y={false,23};apply_common_transform(record,props);
 assert(layouts==0 && object.pivot_x==17 && object.pivot_y==23);
 props={};apply_common_transform(record,props);
 assert(layouts==0 && object.zoom==256 && object.angle==0 && object.pivot_x==0 && object.pivot_y==0);
 object.width=400;object.height=300;props.angle=-90;props.pivot_x={true,50};props.pivot_y={true,50};apply_common_transform(record,props);
 assert(layouts==0 && LV_COORD_GET_PCT(object.pivot_x)*object.width/100==200 && LV_COORD_GET_PCT(object.pivot_y)*object.height/100==150 && object.angle==-900);
 props.zoom=0;apply_common_transform(record,props);assert(object.zoom==1);
}
'''
    harness = directory / 'transform.cpp'
    harness.write_text(code)
    executable = directory / 'transform'
    subprocess.run(['c++', '-std=c++20', '-I'+str(ROOT / 'firmware/managed_components/lvgl__lvgl'), str(harness), '-o', str(executable)], check=True)
    return subprocess.run([str(executable)], capture_output=True)


class GuiTransformLayoutTest(unittest.TestCase):
    def test_identity_skips_layout_and_transforms_reset(self):
        with tempfile.TemporaryDirectory(prefix='gui-transform-layout-') as name:
            directory = Path(name)
            component = 'espressif__brookesia_gui_lvgl'
            original = ROOT / 'firmware/managed_components' / component
            patched = prepare(original, ROOT / 'firmware/patches' / component / '0.8.5/manifest.json', directory / 'patched')
            self.assertEqual(exercise(patched, directory).returncode, 0)


if __name__ == '__main__':
    unittest.main()
