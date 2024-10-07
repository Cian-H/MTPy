{
  inputs = {
    utils.url = "github:numtide/flake-utils";
  };

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        system = "x86_64-linux";
        config = {
          allowUnfree = true;
          cudaSupport = true;
        };
      };
    in
    {
      devShell = pkgs.mkShell
        {
          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc
          ];
          NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";

          buildInputs = with pkgs; [
            python312
            flatbuffers
          ];
        };
    }
  );
}

