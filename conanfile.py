from conan import ConanFile
from conan.tools.gnu import AutotoolsToolchain
import os, re
import shutil
from conan.tools.files import replace_in_file, rm
from conan.tools.env import Environment
from conan.tools.apple import is_apple_os
from conan.tools.build import build_jobs, cross_building

class FFmpegConan(ConanFile):
    name = "ffmpeg"
    version = "4.4.4"

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
    build_requires = "nasm/[]"
    force_autoreconf = False
    
    
    
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

    @property
    def _arch(self) -> str:
        arch = str(self.settings.arch)
        if re.match("armv8*",  arch): return "aarch64"
        elif re.match("arm.*", arch): return "arm"
        elif re.match("x86", arch): return "x86_32"
        elif re.match("x86_64", arch): return "x86_64"
        else: raise Exception(f"Arch {arch} not matched")
    
    def _build_options(self):
        if not cross_building(self):
            return []            
        s = self.settings
        chost = os.environ["CHOST"]
        
        e = lambda x: os.environ[x] if x in os.environ else "false"
       
        arch = self._arch
        
        if is_apple_os(self):
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
        
        
        
    def configure_autotools(self, tc:AutotoolsToolchain):
        cpp_flag = lambda x: (tc.extra_cflags.append(x), tc.extra_cxxflags.append(x))
        tc.extra_cflags.append(os.environ.get("CFLAGS", ""))
        tc.extra_cxxflags.append(os.environ.get("CXXFLAGS", ""))
        tc.extra_ldflags.append(os.environ.get("LDFLAGS", ""))
        
        #for f in [ "CFLAGS", "CXXFLAGS", "LDFLAGS", "CPPFLAGS", "CXXCPPFLAGS" ]:
        #    if f in os.environ: tc.exappend_def(vars, f, os.environ[f])
            
        debug_prefix_mapping = f'-ffile-prefix-map="{os.path.abspath(self.source_folder)}"="{os.path.join("conan-pkg", self.name)}"'
        cpp_flag(debug_prefix_mapping)
        cpp_flag("-fexceptions")
        
        if self.settings.os == "Linux":
            tc.extra_ldflags.append("-Wl,--enable-new-dtags")
            
        buildStatic = hasattr(self.options, "shared") and not getattr(self.options, "shared")
            
        if hasattr(self.settings, "os") and getattr(self.settings, "os") != "Windows":
            wantsPIC = hasattr(self.options, "fPIC") and getattr(self.options, "fPIC")
            if wantsPIC or not buildStatic:
                cpp_flag("-fPIC")
                                
        
        if self.deps_env_info.SYSROOT:
            if self.settings.compiler in [ "clang", "apple-clang" ] and is_apple_os(self):
                cpp_flag(f"-isysroot {self.deps_env_info.SYSROOT}")                
            else:
                cpp_flag(f"--sysroot={self.deps_env_info.SYSROOT}")

        tc.configure_args.clear()
        if self.settings.arch == "x86": tc.configure_args.append("--disable-asm")
        
        tc.configure_args += [
            "--disable-doc",
            f"--prefix={self.package_folder}",
            *self._std_options(),
            *self._library_options(),
            *self._build_options(),            
        ]
                
        
        
    def build(self):
        tc = self._init_autotools()

        args = list( map(lambda x: f"'{x}'", tc.configure_args) )
        args = " ".join(args)
        
        with self.python_requires["wdyConanHelper"].module.utils.dependencies_environment(self, True).apply():
            
            with tc.environment().vars(self).apply():                
                self.output.info("configure-args: "+args)
                self.run("./configure "+args)
                self.run(f"make -j{build_jobs(self)}")
        
        
    def package(self):
        self.run(f"make install -j{build_jobs(self)}")
        rm(self, "*.la", os.path.join(self.package_folder, "lib"), True)
        

