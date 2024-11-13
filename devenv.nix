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
    llvm_14
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
    llvm_14
    openssl
    stdenv.cc.cc
    systemd
    util-linux
    xz
    zlib
    zstd
  ]);
  env.NIX_LD = lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";

  languages = {
    python = {
      version = "3.12";
      enable = true;
      poetry = {
        enable = true;
      };
    };
  };
}
