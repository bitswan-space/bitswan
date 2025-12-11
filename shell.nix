let pkgs = import <nixpkgs> {};

in pkgs.mkShell {
    buildInputs = with pkgs; [
        python313
        python313Packages.setuptools
        python313Packages.pip
        python313Packages.virtualenv
        python313Packages.numpy
        ruff
    ];

  shellHook = ''
    source .venv/bin/activate
  '';

}

