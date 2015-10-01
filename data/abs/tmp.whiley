import whiley.lang.*

/** 
 * Return the absolute of an integer parameter
 */
function abs(int x) => (int y)
// Return value cannot be negative
ensures y >= 0:
    //
    if x >= 0:
    	return x
    else:
        return -x

public method main(System.Console console):
    console.out.println("abs(1) = " ++ abs(1))
    console.out.println("abs(0) = " ++ abs(0))
    console.out.println("abs(-1) = " ++ abs(-1))
