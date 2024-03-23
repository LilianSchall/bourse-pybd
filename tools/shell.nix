{ pkgs ? import <nixpkgs> {} }:
(pkgs.mkShell {
  name = "pip-env";
  nativeBuildInputs = with pkgs; [
    python3
    python3Packages.pip
    python3Packages.virtualenv
    python3Packages.numpy
    python3Packages.pandas
    evince
  ];
})
