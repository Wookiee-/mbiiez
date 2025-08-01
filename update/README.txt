************************************************************
********** Movie Battles II Crossplatform Updater **********
************************************************************

Requirements:
.NET Core 6.0 or later https://dotnet.microsoft.com/download

Usage:
dotnet MBII_CommandLine_Update_XPlatform.dll

Options:
-help | -?		This help information.
-path | -p      	Path to GameData Folder. If not specified will default to current directory
-count | -c     	Calculate the number of files requiring patching. Can be combined with -repair. -silent implied
-repair | -r    	Force a revalidation according to the normal installation rules.
-silent | -s    	Disable console output.
-beta | -b		Perform desired operation on open beta files
-zip | -z		Install from specified Zip File