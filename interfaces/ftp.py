

from zope.interface import Interface

class IFTPCommandHandler(Interface):
    """This interface defines all the FTP commands that are supported by the
       server.

       Every command takes the command line as first arguments, since it is
       responsible
    """

    def cmd_abor(args):
        """Abort operation. No read access required.
        """

    def cmd_appe(args):
        """Append to a file. Write access required.
        """

    def cmd_cdup(args):
        """Change to parent of current working directory.
        """

    def cmd_cwd(args):
        """Change working directory.
        """

    def cmd_dele(args):
        """Delete a file. Write access required.
        """

    def cmd_help(args):
        """Give help information. No read access required.
        """

    def cmd_list(args):
        """Give list files in a directory or displays the info of one file.
        """

    def cmd_mdtm(args):
        """Show last modification time of file.

           Example output: 213 19960301204320

           Geez, there seems to be a second syntax for this fiel, where one
           can also set the modification time using:
           MDTM datestring pathname

        """

    def cmd_mkd(args):
        """Make a directory. Write access required.
        """

    def cmd_mode(args):
        """Set file transfer mode.  No read access required. Obselete.
        """

    def cmd_nlst(args):
        """Give name list of files in directory.
        """

    def cmd_noop(args):
        """Do nothing. No read access required.
        """

    def cmd_pass(args):
        """Specify password.
        """

    def cmd_pasv(args):
        """Prepare for server-to-server transfer. No read access required.
        """

    def cmd_port(args):
        """Specify data connection port. No read access required.
        """

    def cmd_pwd(args):
        """Print the current working directory.
        """

    def cmd_quit(args):
        """Terminate session. No read access required.
        """

    def cmd_rest(args):
        """Restart incomplete transfer.
        """

    def cmd_retr(args):
        """Retrieve a file.
        """

    def cmd_rmd(args):
        """Remove a directory. Write access required.
        """

    def cmd_rnfr(args):
        """Specify rename-from file name. Write access required.
        """

    def cmd_rnto(args):
        """Specify rename-to file name. Write access required.
        """

    def cmd_size(args):
        """Return size of file.
        """

    def cmd_stat(args):
        """Return status of server. No read access required.
        """

    def cmd_stor(args):
        """Store a file. Write access required.
        """

    def cmd_stru(args):
        """Set file transfer structure. Obselete."""

    def cmd_syst(args):
        """Show operating system type of server system.

           No read access required.

           Replying to this command is of questionable utility,
           because this server does not behave in a predictable way
           w.r.t. the output of the LIST command.  We emulate Unix ls
           output, but on win32 the pathname can contain drive
           information at the front Currently, the combination of
           ensuring that os.sep == '/' and removing the leading slash
           when necessary seems to work.  [cd'ing to another drive
           also works]

           This is how wuftpd responds, and is probably the most
           expected.  The main purpose of this reply is so that the
           client knows to expect Unix ls-style LIST output.

           one disadvantage to this is that some client programs
           assume they can pass args to /bin/ls.  a few typical
           responses:

           215 UNIX Type: L8 (wuftpd)
           215 Windows_NT version 3.51
           215 VMS MultiNet V3.3
           500 'SYST': command not understood. (SVR4)
        """

    def cmd_type(args):
        """Specify data transfer type. No read access required.
        """

    def cmd_user(args):
        """Specify user name. No read access required.
        """



# this is the command list from the wuftpd man page
# '!' requires write access
#
not_implemented_commands = {
        'acct':        'specify account (ignored)',
        'allo':        'allocate storage (vacuously)',
        'site':        'non-standard commands (see next section)',
        'stou':        'store a file with a unique name',                            #!
        'xcup':        'change to parent of current working directory (deprecated)',
        'xcwd':        'change working directory (deprecated)',
        'xmkd':        'make a directory (deprecated)',                            #!
        'xpwd':        'print the current working directory (deprecated)',
        'xrmd':        'remove a directory (deprecated)',                            #!
}
