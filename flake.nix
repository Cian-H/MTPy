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
            NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
              pkgs.arrow-cpp # For pyarrow
              pkgs.stdenv.cc.cc # For cmake
              pkgs.llvm_14 # For llvmlite
              pkgs.python312 # For poetry
              pkgs.zlib # For numpy
            ];
            NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";

            buildInputs =
              (with pkgs; [
                arrow-cpp
                python312
                flatbuffers
                llvm_14
                zlib
              ])
              ++ (with pkgs-unstable; [
                steam-run-free
              ]);
          };
      }
    );
}
