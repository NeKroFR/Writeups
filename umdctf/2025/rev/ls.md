# ls

The challenge provide a binary that creates a parent and child process, where the parent process manipulates the child's syscalls using ptrace mechanism.

On ida we can look at 3 main functions:

```c
__int64 __fastcall main(__int64 argc, char **argv, char **envp)
{
  __pid_t child_pid; // [rsp+Ch] [rbp-4h]

  child_pid = fork();
  if ( child_pid < 0 )
    return 0xFFFFFFFFLL;
  if ( !child_pid )
    child_process();
  parent_process((unsigned int)child_pid, argv);
  return 0LL;
}
```

```c
unsigned __int64 __fastcall parent_process(__pid_t child_pid)
{
  int child_status; // [rsp+14h] [rbp-11Ch] BYREF
  int flag_index; // [rsp+18h] [rbp-118h]
  int v4; // [rsp+1Ch] [rbp-114h]
  _BYTE v5[120]; // [rsp+20h] [rbp-110h] BYREF
  __int64 v6; // [rsp+98h] [rbp-98h]
  char flag_input[40]; // [rsp+100h] [rbp-30h] BYREF
  unsigned __int64 canary; // [rsp+128h] [rbp-8h]

  canary = __readfsqword(0x28u);
  puts("Enter flag to proceed: ");
  fgets(flag_input, 35, stdin);
  flag_index = 0;
  ptrace(PTRACE_SETOPTIONS, (unsigned int)child_pid, 0LL, 0x100000LL);
  waitpid(child_pid, &child_status, 2);
  while ( 1 )
  {
    ptrace(PTRACE_SYSCALL, (unsigned int)child_pid, 0LL, 0LL);
    waitpid(child_pid, &child_status, 0);
    if ( (child_status & 0x7F) == 0 )
      break;
    ptrace(PTRACE_GETREGS, (unsigned int)child_pid, 0LL, v5);
    if ( v6 == 60 || v6 == 231 )
      exit(0);
    v6 ^= flag_input[flag_index++];
    if ( flag_index > 34 )
      exit(0);
    ptrace(PTRACE_SETREGS, (unsigned int)child_pid, 0LL, v5);
    ptrace(PTRACE_SYSCALL, (unsigned int)child_pid, 0LL, 0LL);
    waitpid(child_pid, 0LL, 0);
    v4 = ptrace(PTRACE_GETREGS, (unsigned int)child_pid, 0LL, v5);
    if ( v4 == -1 && *__errno_location() == 3 )
      _exit(0);
  }
  puts("Done!");
  return canary - __readfsqword(0x28u);
}
```

We can see that the parent process xor each syscall numbers with a char from our input:

```c
syscall_number ^= flag_input[flag_index++];
```

I will not provide the full code of the child function, but basically, it contains a series of syscalls and validation checks to be sure that the parent verifyed correctly the syscall with our input.


Now we must guess all the syscall numbers the child process was attempting to make to then retrieve each flag bytes such as:

```c
flag_byte = child_syscall_number ^ intended_syscall_number
```


I first extracted all the syscall numbers from the child process:

```
84, 76, 69, 66, 85, 71, 122, 112, 118, 115, 64, 45, 100, 44, 72, 82, 44, 103, 21, 111, 334, 120, 265, 105, 52, 111, 34, 44, 48, 117, 124
```

Then I guessed the intended syscall
```
1, 1, 1, 1, 1, 1, 1, 0, 2, 1, 33, 78, 1, 1, 33, 33, 1, 1, 96, 1, 293, 1, 292, 0, 1, 1, 9, 1, 1, 1, 1
```

## solve.py

```py
child_syscall_numbers = [84, 76, 69, 66, 85, 71, 122, 112, 118, 115, 64, 45, 100, 44, 72, 82, 44, 103, 21, 111, 334, 120, 265, 105, 52, 111, 34, 44, 48, 117, 124]
intended_syscall_numbers = [1, 1, 1, 1, 1, 1, 1, 0, 2, 1, 33, 78, 1, 1, 33, 33, 1, 1, 96, 1, 293, 1, 292, 0, 1, 1, 9, 1, 1, 1, 1]

flag = ""
for i in range(len(child_syscall_numbers)):
    flag += chr(child_syscall_numbers[i] ^ intended_syscall_numbers[i])
print(flag)
```
