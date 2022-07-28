from conans import ConanFile, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment
from conans.errors import ConanInvalidConfiguration
import os, re
import shutil
from conan.tools.files import replace_in_file
from conan.tools.env import Environment

class FFmpegConan(ConanFile):
    name = "ffmpeg"
    version = "4.4.1"

    description = "A complete, cross-platform solution to record, convert and stream audio and video"
    topics = ("audio", "video")
    url = "https://gitlab.worldiety.net/worldiety/customer/wdy/libriety/cpp/forks"
    homepage = "https://ffmpeg.org/"
    license = "LGPL 2.1"
        
    settings = "os", "arch", "compiler", "build_type"
    exports_sources = "*", "!autom4te.cache"
    python_requires = "wdyConanHelper/[]"
    python_requires_extend = "wdyConanHelper.ConanAutotools"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,    
    }
    
    
    
    # These could be configurable by conan options
    def _library_options(self):
        return [
            "--disable-demuxers",
            "--disable-muxers",
            "--disable-bsfs",
            "--disable-parsers",
            "--disable-decoders",
            "--disable-encoders",
            "--disable-filters",
            "--disable-protocols",
            "--enable-decoder=mpegvideo",
            "--enable-decoder=mpeg2video",
            "--enable-decoder=mpeg4",
            "--enable-encoder=mpeg4",
            "--enable-decoder=h264",
            "--enable-encoder=ac3",
            "--enable-decoder=h263",
            "--enable-decoder=wmv1",
            "--enable-decoder=wmv2",
            "--enable-decoder=wmv3",
            "--enable-decoder=libvpx_vp8",
            "--enable-encoder=libvpx_vp8",
            "--enable-decoder=libvpx_vp9",
            "--enable-encoder=aac",
            "--enable-decoder=aac",
            "--enable-decoder=vp8",
            "--enable-decoder=hevc",
            "--enable-decoder=wmav1",
            "--enable-decoder=wmav2",
            "--enable-decoder=wmavoice",
            "--enable-demuxer=matroska",
            "--enable-demuxer=webm_dash_manifest",
            "--enable-demuxer=mpegps",
            "--enable-demuxer=mpegts",
            "--enable-demuxer=mpegtsraw",
            "--enable-demuxer=mpegvideo",
            "--enable-demuxer=h264",
            "--enable-muxer=h264",
            "--enable-muxer=mp4",
            "--enable-demuxer=asf",
            "--enable-demuxer=h263",
            "--enable-demuxer=mov",
            "--enable-demuxer=avi",
            "--enable-parser=mpeg4video",
            "--enable-parser=mpegvideo",
            "--enable-parser=h263",
            "--enable-parser=h264",
            "--enable-parser=hevc",
            "--enable-parser=vp8",
            "--enable-parser=vp9",
            "--enable-filter=scale",
            "--enable-filter=fps",
            "--enable-filter=format",
            "--enable-filter=setsar",
            "--enable-filter=setdar",
            "--enable-filter=settb",
            "--enable-filter=setpts",
            "--enable-filter=asettb",
            "--enable-filter=aformat",
            "--enable-filter=aresample",
            "--enable-filter=anull",
            "--enable-filter=asetnsamples",
            "--enable-protocol=file",
            "--disable-v4l2-m2m",
            "--disable-libv4l2",
            "--disable-devices",
            "--disable-static",
            "--enable-shared",
            "--enable-pic",
            "--disable-vulkan",
            "--disable-cuda",
            "--enable-lto",
            "--disable-vdpau",
        ]
        
    def _build_options(self):
        if not tools.cross_building(self):
            return []            
        s = self.settings
        chost = os.environ["CHOST"]
        
        e = lambda x: os.environ[x] if x in os.environ else "false"
       
        if s.os == "Android":
            arch = re.match("([^-]+)-.*", e("CC")).group(1)
        else:
            arch = re.match("([^-]+)-.*", chost).group(1)
        
        if tools.is_apple_os(s.os):
            target_os = "darwin"
        elif s.os == "Windows":
            target_os = "mingw64"
        else:
            target_os = str(s.os).lower()
        
        windres = "false"
        if "WINDRES" in os.environ and "RCFLAGS" in os.environ:
            windres = f'{os.environ["WINDRES"]} {os.environ["RCFLAGS"]}'

        return [
            "--enable-cross-compile",
            f"--cross-prefix={chost}-",
            f"--arch={arch}",
            f"--target-os={target_os}",
            f'--nm={e("NM")}',
            f'--ar={e("AR")}',
#            f'--as={e("AS")}',
            f'--strip={e("STRIP")}',
            f'--windres={windres}',
            f'--cc={e("CC")}',
            f'--cxx={e("CXX")}',
            f'--ld={e("CC")}',
            f'--ranlib={e("RANLIB")}',
        ]

    def _std_options(self):
        opts = []
        if self.options.fPIC:
            opts.append("--enable-pic")
        if self.options.shared:
            opts = [ *opts, "--enable-shared", "--disable-static" ]
        else:
            opts = [ *opts, "--disable-shared", "--enable-static" ]
        return opts
        
        
        
    def configure_env(self):
        vars = self.configure_vars()
        for f in [ "CFLAGS", "CXXFLAGS", "LDFLAGS", "CPPFLAGS", "CXXCPPFLAGS" ]:
            if f in os.environ: self._append_def(vars, f, os.environ[f])
            
        debug_prefix_mapping = f'-ffile-prefix-map="{os.path.abspath(self.source_folder)}"="{os.path.join("conan-pkg", self.name)}"'
        self._append_def(vars, "CFLAGS", debug_prefix_mapping)
        self._append_def(vars, "CXXFLAGS", debug_prefix_mapping)

        self._append_def(vars, "CFLAGS", "-fexceptions")
        self._append_def(vars, "CXXFLAGS", "-fexceptions")
        
        if self.settings.os == "Linux":
            self._append_def(vars, "LDFLAGS", "-Wl,--enable-new-dtags")
            
        buildStatic = hasattr(self.options, "shared") and not getattr(self.options, "shared")
            
        if hasattr(self.settings, "os") and getattr(self.settings, "os") != "Windows":
            wantsPIC = hasattr(self.options, "fPIC") and getattr(self.options, "fPIC")
            if wantsPIC or not buildStatic:
                self._append_def(vars, "CFLAGS", "-fPIC")
                self._append_def(vars, "CXXFLAGS", "-fPIC")
                
        return vars
        
        
        
    def configure_args(self):
        return [
            f"'--prefix={self.package_folder}'",
            *self._std_options(),
            *self._library_options(),
            *self._build_options(),            
        ]
        
        
    def build(self):
        args = list( map(lambda x: f"'{x}'", self.configure_args()) )
        args = " ".join(args)
        
        with self.python_requires["wdyConanHelper"].module.utils.dependencies_environment(self, True).apply():
            
            v = self.configure_env()            
            if self.deps_env_info.SYSROOT:
                if self.settings.compiler in [ "clang", "apple-clang" ] and tools.is_apple_os(self.settings.os):
                    self._append_def(v, "CFLAGS", f"-isysroot {self.deps_env_info.SYSROOT}")
                    self._append_def(v, "CXXFLAGS", f"-isysroot {self.deps_env_info.SYSROOT}")
                else:
                    self._append_def(v, "CFLAGS", f"--sysroot={self.deps_env_info.SYSROOT}")
                    self._append_def(v, "CXXFLAGS", f"--sysroot={self.deps_env_info.SYSROOT}")

            env = Environment()
            for k,v in v.items():
                env.define(k, v)
                
            with env.vars(self).apply():
                self.output.info("configure-args: "+args)
                self.run("./configure "+args)
                self.run(f"make -j{tools.cpu_count()}")
        
        
    def package(self):
        self.run(f"make install -j{tools.cpu_count()}")
        tools.remove_files_by_mask(os.path.join(self.package_folder, "lib"), "*.la")
        

