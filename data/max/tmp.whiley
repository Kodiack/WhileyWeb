import whiley.lang.*

/** 
 * The max() function, which returns the greater 
 * of two integer arguments
 */
function max(int x, int y) => (int r)
// result must be one of the arguments
ensures r == x || r == y
// result must be greater-or-equal than arguments
ensures r >= x && r >= y:
    //
    if x > y:
    	return x
    else:
        return y

method main(System.Console console):
    console.out.println("max(10,0) = " ++ max(10,0))
    console.out.println("max(5,6) = " ++ max(5,6))
    console.out.println("max(0,0) = " ++ max(0,0))
