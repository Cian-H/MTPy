{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  packages = with pkgs; [
    act
    arrow-cpp
    flatbuffers
    git
    zlib
  ];

  env.NIX_LD_LIBRARY_PATH = lib.makeLibraryPath (with pkgs; [
    acl
    act
    arrow-cpp
    attr
    bzip2
    curl
    libsodium
    libssh
    libxml2
    openssl
    ruff
    stdenv.cc.cc
    systemd
    ty
    util-linux
    xz
    zlib
    zstd
  ]);
  env.NIX_LD = lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";

  languages = {
    python = {
      version = "3.14";
      enable = true;
      uv = {
        enable = true;
      };
    };
    rust.enable = true;
  };
}
