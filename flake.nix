{
  inputs = {
    utils.url = "github:numtide/flake-utils";
  };

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
    nixpkgs-unstable,
    utils,
  }:
    utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          system = "x86_64-linux";
          config = {
            allowUnfree = true;
            cudaSupport = true;
          };
        };
        pkgs-unstable = import nixpkgs-unstable {
          system = "x86_64-linux";
          config = {
            allowUnfree = true;
            cudaSupport = true;
          };
        };
      in {
        devShell =
          pkgs.mkShell
          {
            NIX_LD_LIBRARY_PATH = with pkgs;
              lib.makeLibraryPath [
                acl
                arrow-cpp
                attr
                bzip2
                curl
                libsodium
                libssh
                libxml2
                llvm_14
                openssl
                python312
                stdenv.cc.cc
                systemd
                util-linux
                xz
                zlib
                zstd
              ];
            NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";

            buildInputs =
              (with pkgs; [
                arrow-cpp
                flatbuffers
                llvm_14
                python312
                zlib
              ])
              ++ (with pkgs-unstable; [
                steam-run-free
              ]);
          };
      }
    );
}
