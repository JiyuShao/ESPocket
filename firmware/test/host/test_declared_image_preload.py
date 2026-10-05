"""Replay animation source changes through the locked GUI resource Owner."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_gui_interface'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_gui_interface/0.8.2/manifest.json'


def exercise(source, directory):
    text = (source / 'src/runtime_document.cpp').read_text()
    start = text.index('std::expected<void, std::string> Runtime::Impl::update_image_source(')
    end = text.index('std::expected<RuntimeImageResource, std::string> Runtime::Impl::resolve_image_resource_by_id(', start)
    release_start = text.index('void Runtime::Impl::release_image_resource_from_tree(')
    release_end = text.index('bool Runtime::Impl::tree_references_image_resource_except(', release_start)
    methods = text[release_start:release_end] + text[start:end]
    code = r'''
#include <algorithm>
#include <cassert>
#include <expected>
#include <string>
#include <string_view>
#include <vector>
enum class NodeType {Image, Label};
enum class ImagePreloadOwner {Automatic, Manual, All};
struct RuntimeImageResource {std::string id, primary_src; int native_src=0; bool preload=false;};
struct ImageProps {std::string src;};
struct ResolvedImageSpec {std::string primary_src;};
struct Node {NodeType type=NodeType::Image;};
struct NodeRecord {
 Node value; ImageProps image; ResolvedImageSpec resolved;
 Node& node(){return value;} ImageProps& mutable_image_props(){return image;}
 ResolvedImageSpec& mutable_resolved_image(){return resolved;}
};
struct PreloadedImageRecord {RuntimeImageResource resource; unsigned automatic_ref_count=1,manual_ref_count=0;};
struct TreeRecord {std::vector<PreloadedImageRecord> preloaded_images;};
struct Backend {int loads=0,releases=0;void release_image_resource(const RuntimeImageResource&){++releases;}};
struct Runtime {struct Impl {
 Backend* backend; bool referenced=false; bool fail_preload=false;
 static bool is_same_image_resource(const RuntimeImageResource&a,const RuntimeImageResource&b){return a.primary_src==b.primary_src&&a.native_src==b.native_src;}
 RuntimeImageResource make_runtime_image_resource(const ImageProps&p,const ResolvedImageSpec&r){return {p.src,r.primary_src};}
 ResolvedImageSpec resolve_image_spec(TreeRecord&,const std::string&s){return {s};}
 bool should_preload_image_resource_automatically(const RuntimeImageResource&) {return true;}
 bool has_preloaded_image_resource(const TreeRecord&t,const RuntimeImageResource&r){return std::any_of(t.preloaded_images.begin(),t.preloaded_images.end(),[&](const auto&p){return is_same_image_resource(p.resource,r);});}
 std::expected<void,std::string> preload_image_resource_for_tree(TreeRecord&t,const RuntimeImageResource&r,ImagePreloadOwner){
  if(fail_preload)return std::unexpected("allocation failed");
  ++backend->loads;t.preloaded_images.push_back({r});return {};
 }
 bool tree_references_image_resource_except(const TreeRecord&,const NodeRecord&,const std::string&,const RuntimeImageResource&){return referenced;}
 void release_image_resource_from_tree(TreeRecord&,const RuntimeImageResource&,ImagePreloadOwner);
 std::expected<void,std::string> update_image_source(TreeRecord&,NodeRecord&,std::string_view);
 void release_tree_image_resources(TreeRecord&);
};};
''' + methods + r'''
int main(){Backend backend;Runtime::Impl impl{&backend};TreeRecord tree;
 for(const auto*s:{"bird1","bird2","bird3"})tree.preloaded_images.push_back({{s,s,0,true}});
 NodeRecord bird;bird.image.src="bird1";bird.resolved.primary_src="bird1";
 // Explicit declarations own each resource even when no current node uses it.
 for(int i=0;i<200;++i){assert(impl.update_image_source(tree,bird,"bird"+std::to_string(i%3+1)));}
 assert(backend.loads==0&&backend.releases==0&&tree.preloaded_images.size()==3);
 impl.release_tree_image_resources(tree);assert(tree.preloaded_images.empty()&&backend.releases==3);
 // Ordinary automatically loaded images retain their existing release policy.
 tree.preloaded_images.push_back({{"old","old"}});bird.image.src="old";bird.resolved.primary_src="old";
 assert(impl.update_image_source(tree,bird,"new"));assert(backend.loads==1&&backend.releases==4&&tree.preloaded_images.size()==1);
 impl.referenced=true;assert(impl.update_image_source(tree,bird,"other"));assert(tree.preloaded_images.size()==2);
 // A manual release preserves the independently held automatic reference.
 tree.preloaded_images.front().manual_ref_count=1;
 impl.release_image_resource_from_tree(tree,tree.preloaded_images.front().resource,ImagePreloadOwner::Manual);
 assert(tree.preloaded_images.size()==2);
 // Failed loading rolls back both the source and resolved resource.
 impl.fail_preload=true;assert(!impl.update_image_source(tree,bird,"broken"));assert(bird.image.src=="other"&&bird.resolved.primary_src=="other"&&tree.preloaded_images.size()==2);
 bird.value.type=NodeType::Label;assert(!impl.update_image_source(tree,bird,"invalid"));
 impl.release_tree_image_resources(tree);assert(tree.preloaded_images.empty()&&backend.releases==6);
}
'''
    directory = Path(directory)
    cpp, binary = directory / 'preload.cpp', directory / 'preload'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True).returncode


class DeclaredImagePreloadTest(unittest.TestCase):
    def test_animation_preserves_declared_preloads_until_document_unload(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertNotEqual(exercise(SOURCE, directory), 0)
            patched = prepare(SOURCE, MANIFEST, Path(directory) / 'patched')
            self.assertEqual(exercise(patched, directory), 0)


if __name__ == '__main__':
    unittest.main()
