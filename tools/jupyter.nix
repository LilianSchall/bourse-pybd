{pkgs ? import <nixpkgs>{} }:
with pkgs; # Same for pkgs.
mkShell {
  buildInputs = [
    # Defines a python + set of packages.
    (python3.withPackages (ps: with ps; with python3Packages; [
      jupyter
      ipython

      # Uncomment the following lines to make them available in the shell.
      dash
      matplotlib
      numpy
      pandas
      plotly
      seaborn
    ]))
  ];

  # Automatically run jupyter when entering the shell.
  shellHook = "jupyter notebook";
}
