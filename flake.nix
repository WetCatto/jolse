{
  description = "Machine Learning Project - Road Network Simulation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let 
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          # Python 
          pkgs.python313

          # Development Environment
          pkgs.code-cursor
	  pkgs.python313.pkgs.ipykernel
	  pkgs.python313.pkgs.notebook
	  pkgs.python313.pkgs.pip
	  pkgs.python313.pkgs.mypy
          
          # Numerical Computation
          pkgs.python313.pkgs.numpy
          pkgs.python313.pkgs.scipy
          pkgs.python313.pkgs.polars
          
          # Deep Learning
          pkgs.python313.pkgs.torch
          
          # Visualizations
          pkgs.python313.pkgs.seaborn
          pkgs.python313.pkgs.matplotlib
          pkgs.python313.pkgs.pygame
        ];
      };
    };
}
